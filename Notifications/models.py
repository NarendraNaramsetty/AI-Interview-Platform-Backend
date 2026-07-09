import uuid
from django.db import models
from django.conf import settings
from .constants import (
    NOTIFICATION_TYPE_CHOICES,
    NOTIF_SYSTEM,
    FREQUENCY_CHOICES,
    FREQ_DAILY
)

class Notification(models.Model):
    """
    Logs user notifications (alerts, announcements, RAG evaluation status).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPE_CHOICES,
        default=NOTIF_SYSTEM
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} - Read: {self.is_read}"


class NotificationSetting(models.Model):
    """
    Configuration preferences controlling candidate email and push settings.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    frequency = models.CharField(
        max_length=50,
        choices=FREQUENCY_CHOICES,
        default=FREQ_DAILY
    )

    class Meta:
        verbose_name = "Notification Setting"
        verbose_name_plural = "Notification Settings"

    def __str__(self):
        return f"Settings for {self.user.email}"
