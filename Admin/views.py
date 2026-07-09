from rest_framework import permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse

from users.models import UserProfile
from chatbot.pagination import PrepAIPagination
from .services import AdminService
from .serializers import AdminUserListSerializer

class AdminAnalyticsView(APIView):
    """
    GET /api/admin/analytics
    Returns platform-wide aggregates and MRR tracking.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @extend_schema(
        summary="Get Platform Analytics",
        responses={200: OpenApiResponse(description="Calculated platform aggregates")}
    )
    def get(self, request):
        analytics = AdminService.get_platform_analytics()
        return Response({
            "success": True,
            "message": "Platform analytics retrieved.",
            "data": analytics
        }, status=status.HTTP_200_OK)


class AdminUserListView(generics.ListAPIView):
    """
    GET /api/admin/users
    Lists, searches, and filters registered users.
    """
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'preferred_job_role']
    pagination_class = PrepAIPagination

    def get_queryset(self):
        return UserProfile.objects.select_related('user').all()


class AdminUserDetailView(APIView):
    """
    GET /api/admin/users/{id}
    Retrieves user profile profile details.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @extend_schema(
        summary="Get User Detail Stats",
        responses={200: AdminUserListSerializer}
    )
    def get(self, request, id):
        profile = get_object_or_404(UserProfile, pk=id)
        serializer = AdminUserListSerializer(profile)
        return Response({
            "success": True,
            "message": "User details retrieved.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class AdminExportUsersView(APIView):
    """
    GET /api/admin/exports/users
    Download a CSV file of registered users profiles.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @extend_schema(
        summary="Export Users CSV",
        responses={200: OpenApiResponse(description="CSV File Attachment")}
    )
    def get(self, request):
        return AdminService.export_users_csv()


class AdminExportInterviewsView(APIView):
    """
    GET /api/admin/exports/interviews
    Download a CSV file of all interview session logs.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]

    @extend_schema(
        summary="Export Interviews CSV",
        responses={200: OpenApiResponse(description="CSV File Attachment")}
    )
    def get(self, request):
        return AdminService.export_interviews_csv()
