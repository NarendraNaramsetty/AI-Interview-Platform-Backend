from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Notification, NotificationSetting
from .constants import NOTIF_SYSTEM

class NotificationsService:
    """
    Business layer executing notification logging and updates.
    """

    @classmethod
    def send_notification(cls, user, title: str, message: str, notification_type: str = NOTIF_SYSTEM) -> Notification:
        """
        Action: Log a system alert item for the candidate.
        """
        # Ensure setting profile exists
        cls.get_or_create_settings(user)
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )

    @classmethod
    def mark_as_read(cls, notification_id: int, user) -> Notification:
        """
        Action: Set notification read status to True.
        """
        try:
            notif = Notification.objects.get(pk=notification_id, user=user)
        except Notification.DoesNotExist:
            raise ValidationError("Notification not found.")

        notif.is_read = True
        notif.save()
        return notif

    @classmethod
    def mark_all_read(cls, user) -> int:
        """
        Action: Update all user notifications read status to True. Returns updated count.
        """
        qs = Notification.objects.filter(user=user, is_read=False)
        count = qs.count()
        qs.update(is_read=True)
        return count

    @classmethod
    def get_or_create_settings(cls, user) -> NotificationSetting:
        """
        Action: Fetch or initialize user notification setting toggle options.
        """
        settings, created = NotificationSetting.objects.get_or_create(user=user)
        return settings
