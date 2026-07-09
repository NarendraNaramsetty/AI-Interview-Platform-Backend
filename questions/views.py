from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django.core.exceptions import ValidationError
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
import mimetypes

from .models import (
    QuestionCategory,
    Company,
    JobRole,
    Topic,
    QuestionTag,
    InterviewQuestion,
    QuestionAttachment,
    QuestionHistory
)
from .permissions import IsAdminOrReadOnly
from .filters import InterviewQuestionFilter
from .services import QuestionBankService
from .serializers import (
    QuestionCategorySerializer,
    CompanySerializer,
    JobRoleSerializer,
    TopicSerializer,
    QuestionTagSerializer,
    QuestionAttachmentSerializer,
    QuestionHistorySerializer,
    InterviewQuestionSerializer,
    InterviewQuestionWriteSerializer,
    ImportQuestionsSerializer,
    RandomQuestionsRequestSerializer
)

class QuestionCategoryViewSet(viewsets.ModelViewSet):
    queryset = QuestionCategory.objects.all()
    serializer_class = QuestionCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order']


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class JobRoleViewSet(viewsets.ModelViewSet):
    queryset = JobRole.objects.all()
    serializer_class = JobRoleSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category']


class InterviewQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for InterviewQuestion.
    Handles listing, detail retrieval, creation, updates, and deletion.
    """
    queryset = InterviewQuestion.objects.prefetch_related('attachments').all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = InterviewQuestionFilter
    ordering_fields = ['created_at', 'expected_duration']
    ordering = ['-created_at']
    search_fields = ['question', 'short_description', 'explanation']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InterviewQuestionWriteSerializer
        return InterviewQuestionSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Questions retrieved successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Question retrieved successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)


class SearchQuestionsView(generics.ListAPIView):
    """
    GET /api/questions/search
    Dedicated searching view extending filters sets.
    """
    queryset = InterviewQuestion.objects.all()
    serializer_class = InterviewQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = InterviewQuestionFilter
    search_fields = ['question', 'short_description', 'expected_answer', 'explanation']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "success": True,
            "message": "Search results retrieved successfully.",
            "data": response.data
        }, status=status.HTTP_200_OK)


class RandomQuestionsView(APIView):
    """
    GET /api/questions/random
    Selects and returns randomized prompts based on configurations constraints.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Random Prompts Selection",
        description="Returns randomized lists of matching question bank objects.",
        parameters=[
            OpenApiParameter(name="category_id", description="Category identifier", required=False, type=int),
            OpenApiParameter(name="difficulty", description="Easy / Medium / Hard difficulty", required=False, type=str),
            OpenApiParameter(name="company_id", description="Company reference", required=False, type=int),
            OpenApiParameter(name="role_id", description="Job posting link", required=False, type=int),
            OpenApiParameter(name="count", description="Number of questions to pick (1-30)", required=False, type=int, default=5)
        ],
        responses={200: InterviewQuestionSerializer(many=True)}
    )
    def get(self, request):
        serializer = RandomQuestionsRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        category_id = serializer.validated_data.get('category_id')
        difficulty = serializer.validated_data.get('difficulty')
        company_id = serializer.validated_data.get('company_id')
        role_id = serializer.validated_data.get('role_id')
        count = serializer.validated_data.get('count', 5)

        queryset = InterviewQuestion.objects.filter(is_active=True)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        if role_id:
            queryset = queryset.filter(role_id=role_id)

        # Select randomly
        random_questions = queryset.order_by('?')[:count]
        data = InterviewQuestionSerializer(random_questions, many=True).data
        return Response({
            "success": True,
            "message": "Randomized questions selected successfully.",
            "data": data
        }, status=status.HTTP_200_OK)


class ImportQuestionsView(APIView):
    """
    POST /api/questions/import
    Ingests spreadsheets files, populating the question banks in bulk.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Bulk Import Questions",
        description="Imports questions in bulk from Excel or CSV files. Admin only.",
        request=ImportQuestionsSerializer,
        responses={
            201: OpenApiResponse(description="Import processed."),
            400: OpenApiResponse(description="File validation error.")
        }
    )
    def post(self, request):
        serializer = ImportQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data['file']
        
        try:
            summary = QuestionBankService.import_questions_from_file(file_obj, request.user)
            return Response({
                "success": True,
                "message": "Questions spreadsheet imported processed successfully.",
                "data": summary
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class ExportQuestionsView(APIView):
    """
    GET /api/questions/export
    Downloads question bank lists as Excel/CSV sheets.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Bulk Export Questions",
        description="Exports currently filtered list of questions into CSV or Excel sheets.",
        parameters=[
            OpenApiParameter(name="format", description="csv or excel", required=False, type=str, default='csv'),
            OpenApiParameter(name="category", description="Filter category ID", required=False, type=int),
            OpenApiParameter(name="difficulty", description="Difficulty level", required=False, type=str)
        ]
    )
    def get(self, request):
        export_format = request.query_params.get('export_format', 'csv')
        if export_format not in ['csv', 'excel']:
            export_format = 'csv'

        # Filter the queryset first before export
        filter_set = InterviewQuestionFilter(request.query_params, queryset=InterviewQuestion.objects.all())
        if not filter_set.is_valid():
            return Response({
                "success": False,
                "message": "Filter validation error.",
                "errors": filter_set.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        file_bytes, content_type = QuestionBankService.export_questions_to_bytes(
            filter_set.qs, 
            export_format=export_format
        )

        ext = 'csv' if export_format == 'csv' else 'xlsx'
        filename = f"question_bank_export.{ext}"
        
        response = HttpResponse(file_bytes, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class DuplicateQuestionView(APIView):
    """
    POST /api/questions/{id}/duplicate
    Creates a cloner copy of the question.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @extend_schema(
        summary="Duplicate Question",
        description="Duplicates question attributes, logging history references.",
        responses={201: InterviewQuestionSerializer}
    )
    def post(self, request, id):
        question = get_object_or_404(InterviewQuestion, pk=id)
        duplicate = QuestionBankService.duplicate_question(question, request.user)
        
        return Response({
            "success": True,
            "message": "Question duplicated successfully.",
            "data": InterviewQuestionSerializer(duplicate).data
        }, status=status.HTTP_201_CREATED)


class QuestionAttachmentsView(APIView):
    """
    POST /api/questions/{id}/attachments
    GET /api/questions/{id}/attachments
    Uploads supporting attachments or lists attachments.
    """
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        return get_object_or_404(InterviewQuestion, pk=pk)

    @extend_schema(
        summary="List Attachments",
        description="Lists all files uploaded against a specific question.",
        responses={200: QuestionAttachmentSerializer(many=True)}
    )
    def get(self, request, id):
        question = self.get_object(id)
        attachments = question.attachments.all().order_by('-created_at')
        serializer = QuestionAttachmentSerializer(attachments, many=True)
        return Response({
            "success": True,
            "message": "Question attachments fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Upload Attachment",
        description="Uploads images, PDFs, or script templates under 10MB to support prompts.",
        request=QuestionAttachmentSerializer,
        responses={210: QuestionAttachmentSerializer}
    )
    def post(self, request, id):
        # Only admin staff can modify
        if not request.user.is_staff:
            return Response({
                "success": False,
                "message": "Authentication Credentials Missing or Invalid",
                "errors": {"detail": "Admin privileges are required to edit attachments."}
            }, status=status.HTTP_403_FORBIDDEN)

        question = self.get_object(id)
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"file": ["File is required for attachment uploads."]}
            }, status=status.HTTP_400_BAD_REQUEST)

        mime_type, _ = mimetypes.guess_type(file_obj.name)
        file_type = mime_type or 'application/octet-stream'

        try:
            attachment = QuestionAttachment.objects.create(
                question=question,
                file=file_obj,
                file_type=file_type
            )
            
            # Manually trigger a question history change log
            question._history_action = 'Updated'
            question._history_description = f"Added support file attachment '{file_obj.name}'."
            question.save(update_fields=['updated_at'])

            return Response({
                "success": True,
                "message": "Attachment Uploaded Successfully",
                "data": QuestionAttachmentSerializer(attachment).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": {"detail": e.messages}
            }, status=status.HTTP_400_BAD_REQUEST)


class QuestionAttachmentDeleteView(APIView):
    """
    DELETE /api/questions/attachments/{id}
    Removes supporting attachments.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @extend_schema(
        summary="Delete Attachment",
        description="Removes supporting images or PDF sheets.",
        responses={200: OpenApiResponse(description="Deleted successfully.")}
    )
    def delete(self, request, id):
        attachment = get_object_or_404(QuestionAttachment, pk=id)
        question = attachment.question
        
        filename = attachment.file.name
        attachment.file.delete()  # Remove binary file from disk
        attachment.delete()

        # Log change action
        question._history_action = 'Updated'
        question._history_description = f"Removed support file attachment '{filename}'."
        question.save(update_fields=['updated_at'])

        return Response({
            "success": True,
            "message": "Attachment deleted successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)


class QuestionHistoryView(APIView):
    """
    GET /api/questions/{id}/history
    Lists history updates logs.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Modification History Logs",
        description="Chronological log trace of duplicating, updating, importing, or editing the question.",
        responses={200: QuestionHistorySerializer(many=True)}
    )
    def get(self, request, id):
        question = get_object_or_404(InterviewQuestion, pk=id)
        logs = question.history_logs.all().order_by('-timestamp')
        serializer = QuestionHistorySerializer(logs, many=True)
        return Response({
            "success": True,
            "message": "Question history log retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
