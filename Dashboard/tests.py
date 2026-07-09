from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from users.models import UserProfile

User = get_user_model()

class DashboardTests(APITestCase):
    """
    Unit tests verifying combined candidate dashboard metrics lookup and activity feeds.
    """

    def setUp(self):
        self.candidate = User.objects.create_user(
            email='candidate@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Candidate'
        )

        self.profile = self.candidate.profile
        self.profile.experience_level = 'Medium'
        self.profile.preferred_job_role = 'Backend Developer'
        self.profile.save()

        self.stats = self.candidate.statistics
        self.stats.highest_score = 120.0
        self.stats.save()

        self.stats_url = reverse('dashboard_stats')
        self.activity_url = reverse('dashboard_activity')

    def test_dashboard_stats(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['data']
        self.assertEqual(data['profile']['ranking_points'], 120)
        self.assertEqual(data['profile']['target_role'], 'Backend Developer')
        self.assertEqual(data['resumes']['total_resumes'], 0)

    def test_dashboard_activity_feed(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.get(self.activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 0)
