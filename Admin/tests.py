from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from users.models import UserProfile

User = get_user_model()

class AdminTests(APITestCase):
    """
    Unit tests for system-wide statistics metrics, candidate lists, exports,
    and staff permission controls.
    """

    def setUp(self):
        # Create users
        self.candidate = User.objects.create_user(
            email='candidate@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Candidate'
        )

        self.admin = User.objects.create_user(
            email='admin@prepai.dev',
            password='AdminPassword123!',
            first_name='Bob',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )

        self.profile = self.candidate.profile
        self.profile.experience_level = 'Junior'
        self.profile.preferred_job_role = 'Python Engineer'
        self.profile.save()

        self.stats = self.candidate.statistics
        self.stats.highest_score = 100.0
        self.stats.save()

        # URL paths
        self.analytics_url = reverse('admin_analytics')
        self.users_list_url = reverse('admin_users_list')
        self.user_detail_url = reverse('admin_user_detail', args=[self.profile.id])
        self.export_users_url = reverse('admin_export_users')
        self.export_interviews_url = reverse('admin_export_interviews')

    def test_candidate_forbidden_access(self):
        # Candidates must be blocked with 403 Forbidden
        self.client.force_authenticate(user=self.candidate)
        
        response = self.client.get(self.analytics_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(self.users_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_analytics_and_listings(self):
        self.client.force_authenticate(user=self.admin)

        # Analytics
        response = self.client.get(self.analytics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_users'], 2)

        # Search list
        response = self.client.get(self.users_list_url, {'search': 'Alice'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

        # User detail
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['target_role'], 'Python Engineer')

    def test_csv_exports(self):
        self.client.force_authenticate(user=self.admin)

        # Export users CSV
        response = self.client.get(self.export_users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

        # Export interviews CSV
        response = self.client.get(self.export_interviews_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
