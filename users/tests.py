from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import UserProfile, UserStatistics, Achievement, UserAchievement, UserPreference

User = get_user_model()

class UsersModuleTests(APITestCase):
    """
    Unit test suite covering profile editing, avatar uploads, statistics,
    achievements, leaderboard sorting, skills JSON lists, and preferences.
    """

    def setUp(self):
        # Create default users
        self.user1 = User.objects.create_user(
            email='alice@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Developer'
        )
        self.user2 = User.objects.create_user(
            email='bob@prepai.dev',
            password='SecurePassword456!',
            first_name='Bob',
            last_name='Architect'
        )
        
        # Profile, Stats, and Preferences are automatically created via signals.
        self.profile_url = reverse('user_profile')
        self.avatar_url = reverse('user_avatar_upload')
        self.stats_url = reverse('user_statistics')
        self.achievements_url = reverse('user_achievements')
        self.leaderboard_url = reverse('user_leaderboard')
        self.skills_url = reverse('user_skills')
        self.preferences_url = reverse('user_preferences')
        self.dashboard_url = reverse('user_dashboard_summary')

    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['user']['email'], 'alice@prepai.dev')

    def test_update_profile_valid(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'headline': 'Experienced Backend Engineer',
            'university': 'MIT',
            'graduation_year': 2024,
            'cgpa': 9.2,
            'location': 'San Francisco'
        }
        response = self.client.put(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['headline'], 'Experienced Backend Engineer')
        self.assertEqual(response.data['data']['cgpa'], 9.2)

    def test_update_profile_invalid_cgpa(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'cgpa': 12.5  # CGPA must be between 0.0 and 10.0
        }
        response = self.client.put(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('cgpa', response.data['errors'])

    def test_update_profile_invalid_graduation_year(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'graduation_year': 1930  # Year must be >= 1950
        }
        response = self.client.put(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('graduation_year', response.data['errors'])

    def test_get_statistics(self):
        # Update user stats directly
        stats = self.user1.statistics
        stats.total_interviews = 5
        stats.completed_interviews = 4
        stats.average_score = 82.5
        stats.save()
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_interviews'], 5)
        self.assertEqual(response.data['data']['average_score'], 82.5)

    def test_get_achievements(self):
        achievement = Achievement.objects.create(
            title='Quick Starter',
            description='Complete your first interview simulation.',
            badge_icon='zap',
            points=50,
            category='Simulation'
        )
        UserAchievement.objects.create(user=self.user1, achievement=achievement)
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.achievements_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['achievement']['title'], 'Quick Starter')

    def test_leaderboard_ordering(self):
        # Set stats for User 1
        stats1 = self.user1.statistics
        stats1.average_score = 91.0
        stats1.save()
        
        # Set stats for User 2
        stats2 = self.user2.statistics
        stats2.average_score = 75.0
        stats2.save()

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.leaderboard_url, {'ordering': '-user__statistics__average_score'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Alice (91.0) should be first, Bob (75.0) second
        results = response.data['data']['results']
        self.assertEqual(results[0]['user']['email'], 'alice@prepai.dev')
        self.assertEqual(results[1]['user']['email'], 'bob@prepai.dev')

    def test_skills_crud_workflow(self):
        self.client.force_authenticate(user=self.user1)
        
        # 1. Get initial skills (empty)
        response = self.client.get(self.skills_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data'], [])
        
        # 2. Add a skill
        response = self.client.post(self.skills_url, {'name': 'Django'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['name'], 'Django')
        skill_id = response.data['data']['id']
        
        # 3. Update the skill
        detail_url = reverse('user_skills_detail', args=[skill_id])
        response = self.client.put(detail_url, {'name': 'Django REST Framework'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], 'Django REST Framework')
        
        # 4. Delete the skill
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. Verify empty list again
        response = self.client.get(self.skills_url)
        self.assertEqual(response.data['data'], [])

    def test_preferences_update(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'dark_mode': False,
            'interview_difficulty': 'Expert',
            'language': 'Spanish'
        }
        response = self.client.put(self.preferences_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['dark_mode'])
        self.assertEqual(response.data['data']['interview_difficulty'], 'Expert')
        self.assertEqual(response.data['data']['language'], 'Spanish')

    def test_dashboard_summary_payload(self):
        stats = self.user1.statistics
        stats.current_streak = 4
        stats.save()
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['current_streak'], 4)
        self.assertIn('profile_completion_percentage', response.data['data'])
        self.assertIn('recommended_next_action', response.data['data'])

    def test_public_profile_lookups(self):
        profile = self.user1.profile
        profile.headline = 'Public Headline'
        profile.location = 'Paris'
        profile.save()
        
        public_url = reverse('public_profile', args=['alice@prepai.dev'])
        
        # Fetch anonymously (No authentication)
        response = self.client.get(public_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['headline'], 'Public Headline')
        self.assertEqual(response.data['data']['location'], 'Paris')
        # Ensure private attributes (like target_package, timezone) are excluded
        self.assertNotIn('target_package', response.data['data'])
        self.assertNotIn('timezone', response.data['data'])
