from rest_framework import permissions, status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Notification, NotificationSetting
from .services import NotificationsService
from .serializers import NotificationSerializer, NotificationSettingSerializer
from .filters import NotificationFilter
from chatbot.pagination import PrepAIPagination # reuse our clean chatbot pagination class!

class NotificationListView(generics.ListAPIView):
    """
    GET /api/notifications
    Lists user's notifications. Supports pagination and filters by is_read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = NotificationFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    pagination_class = PrepAIPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    """
    POST /api/notifications/{id}/read
    Marks specific notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Mark Notification Read",
        responses={200: NotificationSerializer}
    )
    def post(self, request, id):
        try:
            notif = NotificationsService.mark_as_read(id, request.user)
            serializer = NotificationSerializer(notif)
            return Response({
                "success": True,
                "message": "Notification marked as read.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except (DjangoValidationError, DRFValidationError) as e:
            err_detail = e.message_dict if hasattr(e, 'message_dict') else e.detail
            return Response({
                "success": False,
                "message": "Validation Error",
                "errors": err_detail
            }, status=status.HTTP_400_BAD_REQUEST)


class MarkAllNotificationsReadView(APIView):
    """
    POST /api/notifications/read-all
    Marks all user's notifications as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Mark All Notifications Read",
        responses={200: OpenApiResponse(description="Count of updated notifications")}
    )
    def post(self, request):
        count = NotificationsService.mark_all_read(request.user)
        return Response({
            "success": True,
            "message": "All notifications marked as read.",
            "data": {"count": count}
        }, status=status.HTTP_200_OK)


class NotificationSettingsView(APIView):
    """
    GET /api/notifications/settings
    PUT /api/notifications/settings
    Retrieve or update toggle setting preferences.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Notification Settings",
        responses={200: NotificationSettingSerializer}
    )
    def get(self, request):
        settings = NotificationsService.get_or_create_settings(request.user)
        serializer = NotificationSettingSerializer(settings)
        return Response({
            "success": True,
            "message": "Notification settings retrieved.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Notification Settings",
        request=NotificationSettingSerializer,
        responses={200: NotificationSettingSerializer}
    )
    def put(self, request):
        settings = NotificationsService.get_or_create_settings(request.user)
        serializer = NotificationSettingSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "Notification settings updated.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
