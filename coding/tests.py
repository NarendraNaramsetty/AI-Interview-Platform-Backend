from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    CodingCategory,
    CodingProblem,
    TestCase,
    CodeSubmission,
    CodingScore,
    CodingHistory,
    FavoriteProblem
)
from .constants import (
    STATUS_PENDING,
    STATUS_ACCEPTED,
    STATUS_SUBMITTED
)

User = get_user_model()

class CodingModuleTests(APITestCase):
    """
    Unit test suite covering problem listings, drafts saving, submissions,
    streak calculations, leaderboard scopes, bookmarks, and validations.
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

        # Create Category
        self.category = CodingCategory.objects.create(
            name='Arrays',
            description='Array challenges',
            display_order=1
        )

        # Create Problem
        self.problem = CodingProblem.objects.create(
            title='Two Sum',
            description='Find two indices matching target.',
            problem_statement='Given arrays, find target.',
            difficulty='Easy',
            category=self.category,
            tags=['Arrays', 'Two Pointers'],
            hints=['Try a hash map.'],
            time_limit=1.0,
            memory_limit=256,
            points=10
        )

        # Create Test Cases
        TestCase.objects.create(
            problem=self.problem,
            input_data='[2, 7, 11, 15]\n9',
            expected_output='[0, 1]',
            is_sample=True,
            is_hidden=False
        )

        TestCase.objects.create(
            problem=self.problem,
            input_data='[3, 2, 4]\n6',
            expected_output='[1, 2]',
            is_sample=False,
            is_hidden=True
        )

        # URL paths
        self.categories_url = reverse('coding_categories')
        self.problems_list_url = reverse('coding-problem-list')
        self.problem_detail_url = reverse('coding-problem-detail', args=[self.problem.id])
        self.random_url = reverse('coding_random_problem')
        self.start_url = reverse('coding_start')
        self.save_url = reverse('coding_save')
        self.submit_url = reverse('coding_submit')
        self.history_url = reverse('coding_history')
        self.stats_url = reverse('coding_statistics')
        self.leaderboard_url = reverse('coding_leaderboard')
        self.favorites_url = reverse('coding_favorites_list')

    def test_list_categories_and_problems(self):
        self.client.force_authenticate(user=self.candidate)
        
        # List categories
        response = self.client.get(self.categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Arrays')

        # List problems
        response = self.client.get(self.problems_list_url, {'difficulty': 'Easy'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

        # Problem details
        response = self.client.get(self.problem_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['sample_test_cases']), 1)  # Hidden test cases excluded

        # Random problem
        response = self.client.get(self.random_url, {'difficulty': 'Easy'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['title'], 'Two Sum')

    def test_start_session_and_draft_saving(self):
        self.client.force_authenticate(user=self.candidate)

        # Start coding attempt
        response = self.client.post(self.start_url, {'problem_id': self.problem.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        draft_id = response.data['data']['id']
        draft = CodeSubmission.objects.get(pk=draft_id)
        self.assertEqual(draft.status, STATUS_PENDING)
        self.assertTrue(CodingHistory.objects.filter(submission=draft, action='Problem Started').exists())

        # Save code draft
        source_code = "def two_sum(nums, target):\n    return [0, 1]"
        response = self.client.post(self.save_url, {
            'problem_id': self.problem.id,
            'programming_language': 'Python',
            'source_code': source_code
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CodeSubmission.objects.get(pk=draft_id).source_code, source_code)
        self.assertTrue(CodingHistory.objects.filter(submission=draft, action='Code Saved').exists())

    def test_submit_code_and_acceptance_rate_signal(self):
        self.client.force_authenticate(user=self.candidate)

        source_code = "def two_sum(nums, target):\n    return [0, 1]"
        response = self.client.post(self.submit_url, {
            'problem_id': self.problem.id,
            'programming_language': 'Python',
            'source_code': source_code
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        sub_id = response.data['data']['id']
        submission = CodeSubmission.objects.get(pk=sub_id)
        self.assertEqual(submission.status, STATUS_ACCEPTED)
        
        # Verify placeholder score cards and points generated
        self.assertEqual(submission.score_record.score, 10)
        self.assertEqual(submission.score_record.ranking_points, 10)

        # Verify problem acceptance rate post_save signal fired
        self.problem.refresh_from_db()
        self.assertEqual(self.problem.acceptance_rate, 100.0)

    def test_permissions_access_limits(self):
        self.client.force_authenticate(user=self.candidate)
        
        # Candidate creates submission
        response = self.client.post(self.submit_url, {
            'problem_id': self.problem.id,
            'programming_language': 'Python',
            'source_code': "def two_sum(): pass"
        }, format='json')
        sub_id = response.data['data']['id']

        # Other candidate retrieves details (should be 403)
        self.client.force_authenticate(user=self.other_candidate)
        detail_url = reverse('coding_submission_detail', args=[sub_id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin retrieves detail report successfully
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_statistics_and_streak_dashboards(self):
        self.client.force_authenticate(user=self.candidate)
        
        # Make a mock accepted submission yesterday
        yesterday_sub = CodeSubmission.objects.create(
            user=self.candidate,
            problem=self.problem,
            programming_language='Python',
            source_code="def two_sum(): pass",
            status=STATUS_ACCEPTED
        )
        yesterday_sub.created_at = timezone.now() - timezone.timedelta(days=1)
        yesterday_sub.save()
        
        CodingScore.objects.create(
            submission=yesterday_sub,
            score=10,
            ranking_points=10
        )

        # Make mock submission today
        response = self.client.post(self.submit_url, {
            'problem_id': self.problem.id,
            'programming_language': 'Python',
            'source_code': "def two_sum(): pass"
        }, format='json')

        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['data']
        self.assertEqual(data['problems_solved'], 1)
        self.assertEqual(data['problems_attempted'], 1)
        self.assertEqual(data['current_streak'], 2)  # Consecutive yesterday and today
        self.assertEqual(data['preferred_language'], 'Python')

    def test_leaderboard_period_scopes(self):
        self.client.force_authenticate(user=self.candidate)
        # Create submission and score
        response = self.client.post(self.submit_url, {
            'problem_id': self.problem.id,
            'programming_language': 'Python',
            'source_code': "def two_sum(): pass"
        }, format='json')

        response = self.client.get(self.leaderboard_url, {'period': 'overall'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['points'], 10)

    def test_favorite_problem_endpoints(self):
        self.client.force_authenticate(user=self.candidate)
        fav_detail_url = reverse('coding_favorites_detail', args=[self.problem.id])

        # Add bookmark
        response = self.client.post(fav_detail_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(FavoriteProblem.objects.filter(user=self.candidate, problem=self.problem).exists())

        # List favorites
        response = self.client.get(self.favorites_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

        # Remove bookmark
        response = self.client.delete(fav_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(FavoriteProblem.objects.filter(user=self.candidate, problem=self.problem).exists())
