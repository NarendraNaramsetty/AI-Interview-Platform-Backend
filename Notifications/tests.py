from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import Notification, NotificationSetting
from .constants import NOTIF_SYSTEM, FREQ_WEEKLY

User = get_user_model()

class NotificationsTests(APITestCase):
    """
    Unit tests for notification listings, bulk read statuses, and toggle settings.
    """

    def setUp(self):
        self.candidate = User.objects.create_user(
            email='candidate@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Candidate'
        )

        self.notif = Notification.objects.create(
            user=self.candidate,
            title='Interview Feedback Ready',
            message='Your feedback score is ready.',
            notification_type=NOTIF_SYSTEM,
            is_read=False
        )

        self.list_url = reverse('notifications_list')
        self.read_all_url = reverse('notifications_read_all')
        self.settings_url = reverse('notifications_settings')
        self.mark_read_url = reverse('notifications_mark_read', args=[self.notif.id])

    def test_notification_listings_and_read(self):
        self.client.force_authenticate(user=self.candidate)

        # List
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

        # Mark single read
        response = self.client.post(self.mark_read_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Notification.objects.get(pk=self.notif.id).is_read)

    def test_mark_all_read(self):
        self.client.force_authenticate(user=self.candidate)

        # Mark all read
        response = self.client.post(self.read_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertFalse(Notification.objects.filter(user=self.candidate, is_read=False).exists())

    def test_settings_retrieval_and_update(self):
        self.client.force_authenticate(user=self.candidate)

        # Get settings
        response = self.client.get(self.settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['email_enabled'])

        # Update settings
        response = self.client.put(self.settings_url, {
            'email_enabled': False,
            'frequency': FREQ_WEEKLY
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        setting_obj = NotificationSetting.objects.get(user=self.candidate)
        self.assertFalse(setting_obj.email_enabled)
        self.assertEqual(setting_obj.frequency, FREQ_WEEKLY)
