from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, filters
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import FileResponse
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.core.exceptions import ValidationError

from .models import Resume, ResumeActivity, ResumeAnalysis
from .permissions import IsResumeOwnerOrAdmin
from .services import ResumeService
from .filters import ResumeFilter
from .serializers import (
    ResumeSerializer,
    ResumeDetailSerializer,
    ResumeUploadSerializer,
    ResumeUpdateSerializer,
    ResumeActivitySerializer,
    ResumeAnalysisSerializer
)

class ResumeListView(generics.ListAPIView):
    """
    GET /api/resume/
    Lists all active resumes for the user. Admins can view all records.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResumeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ResumeFilter
    ordering_fields = ['created_at', 'title', 'file_size', 'resume_version']
    ordering = ['-created_at']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Resume.objects.all()
        return Resume.objects.filter(user=self.request.user)

    @extend_schema(
        summary="List Resumes",
        description="Lists metadata records of uploaded active resumes. Supports sorting, searching, and pagination.",
        parameters=[
            OpenApiParameter(name="ordering", description="Order fields: title, created_at, file_size.", required=False, type=str),
            OpenApiParameter(name="title", description="Search by title.", required=False, type=str),
            OpenApiParameter(name="is_default", description="Filter by default status.", required=False, type=bool)
        ]
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Resumes retrieved successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)


class ResumeUploadView(APIView):
    """
    POST /api/resume/upload
    Uploads a new document file, extracts text, counts pages, and saves metadata.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload Resume File",
        description="Accepts PDF/DOCX files up to 10MB, extracts text, and initializes evaluations.",
        request=ResumeUploadSerializer,
        responses={
            201: ResumeDetailSerializer,
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file_obj = serializer.validated_data['file']
        title = serializer.validated_data.get('title', '')
        upload_source = serializer.validated_data.get('upload_source', 'Web')
        
        try:
            resume = ResumeService.process_new_resume(
                user=request.user,
                title=title,
                uploaded_file=file_obj,
                upload_source=upload_source
            )
            return Response({
                "success": True,
                "message": "Resume Uploaded Successfully",
                "data": ResumeDetailSerializer(resume).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class ResumeDetailView(APIView):
    """
    GET /api/resume/{id}
    PUT /api/resume/{id}
    DELETE /api/resume/{id}
    Manages specific resume details, updates, and soft deletions.
    """
    permission_classes = [permissions.IsAuthenticated, IsResumeOwnerOrAdmin]

    def get_object(self, pk):
        resume = get_object_or_404(Resume, pk=pk)
        self.check_object_permissions(self.request, resume)
        return resume

    @extend_schema(
        summary="Get Resume Details",
        description="Retrieves metadata, raw text, and evaluations of the resume.",
        responses={200: ResumeDetailSerializer}
    )
    def get(self, request, id):
        resume = self.get_object(id)
        serializer = ResumeDetailSerializer(resume)
        return Response({
            "success": True,
            "message": "Resume details retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Resume Details",
        description="Allows replacing files (increments version) or changing document title labels.",
        request=ResumeUpdateSerializer,
        responses={200: ResumeDetailSerializer}
    )
    def put(self, request, id):
        resume = self.get_object(id)
        serializer = ResumeUpdateSerializer(resume, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Check replacement file
        file_obj = serializer.validated_data.get('file')
        title = serializer.validated_data.get('title')
        is_default = serializer.validated_data.get('is_default')
        
        try:
            if file_obj:
                resume = ResumeService.replace_resume_file(resume, file_obj)
            if title:
                resume.title = title
                resume.save(update_fields=['title'])
                ResumeService.log_activity(resume, 'Updated Title', f"Renamed resume title to '{title}'.")
            if is_default:
                ResumeService.set_default_resume(resume)
                
            return Response({
                "success": True,
                "message": "Resume updated successfully.",
                "data": ResumeDetailSerializer(resume).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete Resume (Soft Delete)",
        description="Flags the resume deleted_at column; ignores record in general listings.",
        responses={200: OpenApiResponse(description="Resume soft-deleted successfully.")}
    )
    def delete(self, request, id):
        resume = self.get_object(id)
        ResumeService.soft_delete_resume(resume)
        return Response({
            "success": True,
            "message": "Resume Deleted Successfully",
            "data": {}
        }, status=status.HTTP_200_OK)


class ResumeDownloadView(APIView):
    """
    GET /api/resume/{id}/download
    Serves the binary document file as an attachment download response.
    """
    permission_classes = [permissions.IsAuthenticated, IsResumeOwnerOrAdmin]

    @extend_schema(
        summary="Download Resume File",
        description="Downloads the physical PDF/DOCX resume file attachment.",
        responses={200: OpenApiResponse(description="File streamed successfully.")}
    )
    def get(self, request, id):
        resume = get_object_or_404(Resume, pk=id)
        self.check_object_permissions(request, resume)
        
        response = FileResponse(resume.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{resume.original_filename}"'
        
        # Log download action
        ResumeService.log_activity(resume, 'Downloaded Resume', "Downloaded the document file binary.")
        
        return response


class ResumeSetDefaultView(APIView):
    """
    POST /api/resume/{id}/default
    Enforces a default resume tag for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated, IsResumeOwnerOrAdmin]

    @extend_schema(
        summary="Set Default Resume",
        description="Flags this document default, clearing default tags from all other user files.",
        responses={200: OpenApiResponse(description="Default status assigned successfully.")}
    )
    def post(self, request, id):
        resume = get_object_or_404(Resume, pk=id)
        self.check_object_permissions(request, resume)
        
        ResumeService.set_default_resume(resume)
        
        return Response({
            "success": True,
            "message": "Resume set as default successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class ResumeTextView(APIView):
    """
    GET /api/resume/{id}/text
    Returns raw extracted text contents of a document.
    """
    permission_classes = [permissions.IsAuthenticated, IsResumeOwnerOrAdmin]

    @extend_schema(
        summary="Get Extracted Text",
        description="Returns raw text parsed from document headers, tables, and paragraphs.",
        responses={200: OpenApiResponse(description="Raw text retrieved.")}
    )
    def get(self, request, id):
        resume = get_object_or_404(Resume, pk=id)
        self.check_object_permissions(request, resume)
        
        return Response({
            "success": True,
            "message": "Extracted text retrieved successfully.",
            "data": {
                "resume_text": resume.resume_text
            }
        }, status=status.HTTP_200_OK)


class ResumeVersionsView(APIView):
    """
    GET /api/resume/{id}/versions
    Returns previous iterations matching original filenames.
    """
    permission_classes = [permissions.IsAuthenticated, IsResumeOwnerOrAdmin]

    @extend_schema(
        summary="Get Previous Versions",
        description="Returns historical iterations of resumes matching current file labels, including deleted records.",
        responses={200: ResumeSerializer(many=True)}
    )
    def get(self, request, id):
        resume = get_object_or_404(Resume, pk=id)
        self.check_object_permissions(request, resume)
        
        # Look for other versions with matching filename/title, including soft deleted ones!
        versions = Resume.objects.all_with_deleted().filter(
            user=resume.user,
            original_filename=resume.original_filename
        ).exclude(id=resume.id).order_by('-resume_version')
        
        serializer = ResumeSerializer(versions, many=True)
        return Response({
            "success": True,
            "message": "Resume versions retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ResumeActivityView(APIView):
    """
    GET /api/resume/{id}/activity
    Returns user transaction auditing records associated with a resume.
    """
    permission_classes = [permissions.IsAuthenticated, IsResumeOwnerOrAdmin]

    @extend_schema(
        summary="Get Audit Log Activities",
        description="Lists all user actions (upload, download, tag changes) recorded against the document.",
        responses={200: ResumeActivitySerializer(many=True)}
    )
    def get(self, request, id):
        resume = get_object_or_404(Resume, pk=id)
        self.check_object_permissions(request, resume)
        
        activities = resume.activities.all().order_by('-created_at')
        serializer = ResumeActivitySerializer(activities, many=True)
        
        return Response({
            "success": True,
            "message": "Resume activity logs retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class ResumeAnalysisView(APIView):
    """
    GET /api/resume/analysis
    Returns the AI analysis of the user's default (or latest) resume.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Resume AI Analysis",
        description="Returns the AI analysis of the user's default (or latest) resume.",
        responses={200: ResumeAnalysisSerializer}
    )
    def get(self, request):
        # 1. Try default resume
        resume = Resume.objects.filter(user=request.user, is_default=True).first()
        if not resume:
            # 2. Fallback to latest uploaded resume
            resume = Resume.objects.filter(user=request.user).order_by('-created_at').first()
            
        if not resume:
            return Response(
                {"detail": "No resume uploaded yet."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Get or create placeholder analysis
        analysis, _ = ResumeAnalysis.objects.get_or_create(resume=resume)
        
        serializer = ResumeAnalysisSerializer(analysis)
        return Response(serializer.data, status=status.HTTP_200_OK)
