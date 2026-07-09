from .services import RoadmapService
import datetime
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder
)
from .constants import (
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_PAUSED,
    STATUS_NOT_STARTED,
    FREQ_DAILY
)

User = get_user_model()

class RoadmapModuleTests(APITestCase):
    """
    Unit test suite covering Learning Roadmaps, career paths, resources searching,
    streak metrics tracking, reminders CRUD, progress updates, and security constraints.
    """

    def setUp(self):
        # Create users
        self.candidate = User.objects.create_user(
            email='candidate@prepai.dev',
            password='SecurePassword123!',
            first_name='Alice',
            last_name='Candidate'
        )
        self.other_candidate = User.objects.create_user(
            email='other@prepai.dev',
            password='SecurePassword123!',
            first_name='Charlie',
            last_name='Other'
        )
        self.admin = User.objects.create_user(
            email='admin@prepai.dev',
            password='AdminPassword123!',
            first_name='Bob',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )

        # Create Career Path
        self.career = CareerPath.objects.create(
            name='AI Engineer',
            description='Pathway to AI',
            estimated_duration='6 months',
            difficulty='Medium'
        )

        # Create Roadmap
        self.roadmap = Roadmap.objects.create(
            title='Intro to Neural Networks',
            description='Learn core nodes logic.',
            career_path=self.career,
            estimated_duration='24 hours',
            difficulty='Medium',
            total_modules=1
        )

        # Create Roadmap Module
        self.module = RoadmapModule.objects.create(
            roadmap=self.roadmap,
            title='Perceptrons',
            description='Single layer learning.',
            module_order=1,
            estimated_hours=4,
            module_type='Video'
        )

        # Create Learning Resource
        self.resource = LearningResource.objects.create(
            roadmap_module=self.module,
            title='Neural Networks 3Blue1Brown',
            resource_type='YouTube',
            provider='3Blue1Brown',
            url='https://youtube.com/neuralnets',
            duration=20,
            is_free=True
        )

        # URL paths
        self.careers_url = reverse('roadmap_careers')
        self.roadmaps_list_url = reverse('roadmap-item-list')
        self.roadmap_detail_url = reverse('roadmap-item-detail', args=[self.roadmap.id])
        self.start_url = reverse('roadmap_start')
        self.progress_url = reverse('roadmap_progress')
        self.current_url = reverse('roadmap_current')
        self.completed_url = reverse('roadmap_completed')
        self.pause_url = reverse('roadmap_pause')
        self.resume_url = reverse('roadmap_resume')
        self.resources_url = reverse('roadmap_resources')
        self.stats_url = reverse('roadmap_statistics')
        self.reminders_url = reverse('roadmap-reminder-list')

    def test_careers_and_roadmaps_retrieval(self):
        self.client.force_authenticate(user=self.candidate)

        # 1. Careers List
        response = self.client.get(self.careers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'AI Engineer')

        # 2. Roadmaps List
        response = self.client.get(self.roadmaps_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

        # 3. Roadmap Detail
        response = self.client.get(self.roadmap_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Intro to Neural Networks')
        self.assertEqual(len(response.data['modules']), 1)
        self.assertEqual(len(response.data['modules'][0]['resources']), 1)

    def test_start_pause_resume_roadmaps(self):
        self.client.force_authenticate(user=self.candidate)

        # Start Roadmap
        response = self.client.post(self.start_url, {'roadmap_id': self.roadmap.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        user_roadmap_id = response.data['data']['id']
        ur_obj = UserRoadmap.objects.get(pk=user_roadmap_id)
        self.assertEqual(ur_obj.status, STATUS_IN_PROGRESS)

        # Get Current Roadmap
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], user_roadmap_id)

        # Pause Roadmap
        response = self.client.post(self.pause_url, {'roadmap_id': self.roadmap.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ur_obj.refresh_from_db()
        self.assertEqual(ur_obj.status, STATUS_PAUSED)

        # Resume Roadmap
        response = self.client.post(self.resume_url, {'roadmap_id': self.roadmap.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ur_obj.refresh_from_db()
        self.assertEqual(ur_obj.status, STATUS_IN_PROGRESS)

    def test_update_module_progress(self):
        self.client.force_authenticate(user=self.candidate)
        
        # Start roadmap
        response = self.client.post(self.start_url, {'roadmap_id': self.roadmap.id}, format='json')
        user_roadmap_id = response.data['data']['id']

        # Complete Roadmap module progress
        response = self.client.put(self.progress_url, {
            'user_roadmap_id': user_roadmap_id,
            'module_id': self.module.id,
            'is_completed': True,
            'notes': 'Completed neural perceptrons.'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify stats and status values
        ur_obj = UserRoadmap.objects.get(pk=user_roadmap_id)
        self.assertEqual(ur_obj.progress_percentage, 100.0)
        self.assertEqual(ur_obj.status, STATUS_COMPLETED)
        self.assertIsNotNone(ur_obj.completed_at)

        # Completed Roadmaps List
        response = self.client.get(self.completed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_dashboard_statistics_and_streaks(self):
        self.client.force_authenticate(user=self.candidate)
        
        # Setup finished roadmap with completion date yesterday
        user_roadmap = RoadmapService.start_roadmap(self.roadmap.id, self.candidate)
        yesterday = timezone.now() - timezone.timedelta(days=1)
        
        RoadmapService.update_module_progress(
            user_roadmap_id=user_roadmap.id,
            module_id=self.module.id,
            is_completed=True,
            notes='Done yesterday',
            user=self.candidate
        )
        
        # Override completion date in database
        progress = ModuleProgress.objects.get(user_roadmap=user_roadmap, roadmap_module=self.module)
        progress.completion_date = yesterday
        progress.save()

        # Request stats
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['data']
        self.assertEqual(data['hours_learned'], 4)
        self.assertEqual(data['completed_modules'], 1)
        self.assertEqual(data['completed_roadmaps'], 1)
        self.assertEqual(data['learning_streak'], 1)  # Submitted yesterday, so streak=1 (since streak continues to today/yesterday)

    def test_learning_resources_filtering(self):
        self.client.force_authenticate(user=self.candidate)

        response = self.client.get(self.resources_url, {'type': 'YouTube', 'is_free': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_learning_reminders_crud(self):
        self.client.force_authenticate(user=self.candidate)

        # Create reminder
        response = self.client.post(self.reminders_url, {
            'roadmap': self.roadmap.id,
            'reminder_time': '08:30:00',
            'frequency': FREQ_DAILY,
            'is_enabled': True
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reminder_id = response.data['data']['id']

        # List reminders
        response = self.client.get(self.reminders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

        # Update reminder
        detail_url = reverse('roadmap-reminder-detail', args=[reminder_id])
        response = self.client.put(detail_url, {
            'roadmap': self.roadmap.id,
            'reminder_time': '09:00:00',
            'frequency': FREQ_DAILY,
            'is_enabled': False
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(LearningReminder.objects.get(pk=reminder_id).is_enabled)

        # Delete reminder
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(LearningReminder.objects.filter(pk=reminder_id).exists())

    def test_reminder_permissions_limit(self):
        self.client.force_authenticate(user=self.candidate)
        # Candidate creates reminder
        response = self.client.post(self.reminders_url, {
            'roadmap': self.roadmap.id,
            'reminder_time': '10:00:00',
            'frequency': FREQ_DAILY,
            'is_enabled': True
        }, format='json')
        reminder_id = response.data['data']['id']

        # Other candidate attempts to update it (should be 403/404)
        self.client.force_authenticate(user=self.other_candidate)
        detail_url = reverse('roadmap-reminder-detail', args=[reminder_id])
        response = self.client.put(detail_url, {
            'roadmap': self.roadmap.id,
            'reminder_time': '11:00:00',
            'frequency': FREQ_DAILY,
            'is_enabled': False
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
