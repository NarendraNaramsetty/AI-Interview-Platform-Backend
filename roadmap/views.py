from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder
)
from .permissions import IsOwnerOrAdmin
from .filters import RoadmapFilter, LearningResourceFilter
from .services import RoadmapService
from .pagination import PrepAIPagination
from .serializers import (
    StartRoadmapRequestSerializer,
    UpdateProgressRequestSerializer,
    RoadmapActionRequestSerializer,
    CareerPathSerializer,
    LearningResourceSerializer,
    RoadmapSerializer,
    RoadmapDetailSerializer,
    UserRoadmapSerializer,
    LearningReminderSerializer
)
from .constants import STATUS_IN_PROGRESS, STATUS_COMPLETED

class CareerPathListView(generics.ListAPIView):
    """
    GET /api/roadmap/careers
    Lists all active career paths.
    """
    queryset = CareerPath.objects.filter(is_active=True)
    serializer_class = CareerPathSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Careers retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class RoadmapViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/roadmap
    GET /api/roadmap/{id}
    Lists or details roadmaps templates.
    """
    queryset = Roadmap.objects.filter(is_active=True).select_related('career_path')
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = RoadmapFilter
    ordering_fields = ['created_at', 'title']
    ordering = ['title']
    search_fields = ['title', 'description']
    pagination_class = PrepAIPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoadmapDetailSerializer
        return RoadmapSerializer


class StartRoadmapView(APIView):
    """
    POST /api/roadmap/start
    Enrolls a candidate user into a roadmap program.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Start Roadmap Enrolment",
        request=StartRoadmapRequestSerializer,
        responses={201: UserRoadmapSerializer}
    )
    def post(self, request):
        serializer = StartRoadmapRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap_id = serializer.validated_data['roadmap_id']

        try:
            user_roadmap = RoadmapService.start_roadmap(roadmap_id, request.user)
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Roadmap started successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class UpdateProgressView(APIView):
    """
    PUT /api/roadmap/progress
    Updates module progress completions states.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Update Module Learning Progress",
        request=UpdateProgressRequestSerializer,
        responses={200: UserRoadmapSerializer}
    )
    def put(self, request):
        serializer = UpdateProgressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_roadmap_id = serializer.validated_data['user_roadmap_id']
        module_id = serializer.validated_data['module_id']
        is_completed = serializer.validated_data['is_completed']
        notes = serializer.validated_data['notes']

        try:
            user_roadmap = RoadmapService.update_module_progress(
                user_roadmap_id=user_roadmap_id,
                module_id=module_id,
                is_completed=is_completed,
                notes=notes,
                user=request.user
            )
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Module progress updated successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class PauseRoadmapView(APIView):
    """
    POST /api/roadmap/pause
    Pauses active roadmap learning routines.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Pause Active Roadmap",
        request=RoadmapActionRequestSerializer,
        responses={200: UserRoadmapSerializer}
    )
    def post(self, request):
        serializer = RoadmapActionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap_id = serializer.validated_data['roadmap_id']

        try:
            user_roadmap = RoadmapService.pause_roadmap(roadmap_id, request.user)
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Roadmap paused successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class ResumeRoadmapView(APIView):
    """
    POST /api/roadmap/resume
    Resumes paused roadmap progress.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Resume Paused Roadmap",
        request=RoadmapActionRequestSerializer,
        responses={200: UserRoadmapSerializer}
    )
    def post(self, request):
        serializer = RoadmapActionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap_id = serializer.validated_data['roadmap_id']

        try:
            user_roadmap = RoadmapService.resume_roadmap(roadmap_id, request.user)
            response_serializer = UserRoadmapSerializer(user_roadmap)
            return Response({
                "success": True,
                "message": "Roadmap resumed successfully.",
                "data": response_serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrentRoadmapView(APIView):
    """
    GET /api/roadmap/current
    Returns currently active UserRoadmap (status: 'In Progress').
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Current Active Roadmap Progress",
        responses={200: UserRoadmapSerializer}
    )
    def get(self, request):
        current_roadmap = UserRoadmap.objects.filter(
            user=request.user, 
            status=STATUS_IN_PROGRESS
        ).select_related('roadmap').first()
        
        if not current_roadmap:
            return Response({
                "success": True,
                "message": "No active roadmap found.",
                "data": None
            }, status=status.HTTP_200_OK)

        serializer = UserRoadmapSerializer(current_roadmap)
        return Response({
            "success": True,
            "message": "Current roadmap retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CompletedRoadmapsListView(generics.ListAPIView):
    """
    GET /api/roadmap/completed
    Lists completed roadmaps templates for the candidate.
    """
    serializer_class = UserRoadmapSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return UserRoadmap.objects.filter(
            user=self.request.user, 
            status=STATUS_COMPLETED
        ).select_related('roadmap')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Completed roadmaps retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class LearningResourceListView(generics.ListAPIView):
    """
    GET /api/roadmap/resources
    Returns learning study resources filtered by type, provider, or free/paid.
    """
    queryset = LearningResource.objects.all()
    serializer_class = LearningResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = LearningResourceFilter
    search_fields = ['title', 'provider']
    pagination_class = PrepAIPagination

    # Wrap the paginated response in standard success envelope
    # Note: DRF's list triggers paginate_queryset which hooks into PrepAIPagination.


class LearningStatisticsView(APIView):
    """
    GET /api/roadmap/statistics
    Returns user learning metrics stats.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get learning progress statistics",
        responses={200: OpenApiResponse(description="Calculated statistics values")}
    )
    def get(self, request):
        stats = RoadmapService.get_roadmap_statistics(request.user)
        return Response({
            "success": True,
            "message": "Learning statistics retrieved successfully.",
            "data": stats
        }, status=status.HTTP_200_OK)


class LearningReminderViewSet(viewsets.ModelViewSet):
    """
    GET /api/roadmap/reminders
    POST /api/roadmap/reminders
    PUT /api/roadmap/reminders/{id}
    DELETE /api/roadmap/reminders/{id}
    """
    serializer_class = LearningReminderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = 'id'

    def get_queryset(self):
        return LearningReminder.objects.filter(user=self.request.user).select_related('roadmap')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "message": "Reminders retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "success": True,
            "message": "Learning reminder created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "Learning reminder updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "success": True,
            "message": "Learning reminder deleted successfully.",
            "data": {}
        }, status=status.HTTP_200_OK)
