from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile, UserStatistics, UserPreference

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_data(sender, instance, created, **kwargs):
    """
    Auto-creates UserProfile, UserStatistics, and UserPreference
    records whenever a new CustomUser is created.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
        UserStatistics.objects.get_or_create(user=instance)
        UserPreference.objects.get_or_create(user=instance)
