from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from interviews.models import InterviewSession
from .models import (
    InterviewEvaluation,
    TechnicalEvaluation,
    CommunicationEvaluation,
    HRBehaviorEvaluation,
    OverallEvaluation,
    ImprovementSuggestion,
    RecommendedResource,
    EvaluationHistory
)
from .constants import (
    STATUS_PENDING,
    STATUS_COMPLETED,
    RATING_GOOD,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    RESOURCE_COURSE
)

User = get_user_model()

class FeedbackModuleTests(APITestCase):
    """
    Unit test suite covering Feedback & AI Evaluation CRUD, validations,
    access control rules, signals history logging, and PDF download stream.
    """

    def setUp(self):
        # Create candidate users
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

        # Create Interview Sessions
        self.completed_session = InterviewSession.objects.create(
            user=self.candidate,
            title='Python Backend Session',
            target_role='Python Engineer',
            target_company='PrepAI',
            interview_type='Technical',
            difficulty='Medium',
            interview_mode='Text',
            total_questions=5,
            duration_minutes=30,
            status='Completed',
            started_at=timezone.now() - timezone.timedelta(minutes=30),
            completed_at=timezone.now()
        )

        self.incomplete_session = InterviewSession.objects.create(
            user=self.candidate,
            title='Java Frontend Session',
            target_role='Java Developer',
            target_company='PrepAI',
            interview_type='Mixed',
            difficulty='Easy',
            interview_mode='Text',
            total_questions=5,
            duration_minutes=30,
            status='Scheduled'
        )

        # Pre-generate evaluation for some tests
        self.generate_url = reverse('evaluation_generate')

    def test_generate_evaluation_success(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.post(self.generate_url, {'interview_id': self.completed_session.id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify database structures created
        evaluation = InterviewEvaluation.objects.get(interview=self.completed_session)
        self.assertEqual(evaluation.evaluation_status, 'Completed')
        self.assertEqual(evaluation.technical_evaluation.technical_score, 78)
        self.assertEqual(evaluation.communication_evaluation.communication_score, 82)
        self.assertEqual(evaluation.hr_evaluation.confidence_score, 88)
        self.assertEqual(evaluation.overall_evaluation.overall_score, 81)
        self.assertEqual(evaluation.suggestions.count(), 2)
        self.assertEqual(evaluation.resources.count(), 2)
        self.assertEqual(evaluation.history_logs.count(), 1)

    def test_generate_evaluation_fails_incomplete_interview(self):
        self.client.force_authenticate(user=self.candidate)
        response = self.client.post(self.generate_url, {'interview_id': self.incomplete_session.id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn("incomplete", str(response.data['errors']))

    def test_permissions_access_limits(self):
        # 1. Generate evaluation
        self.client.force_authenticate(user=self.candidate)
        self.client.post(self.generate_url, {'interview_id': self.completed_session.id}, format='json')
        evaluation = InterviewEvaluation.objects.get(interview=self.completed_session)

        # 2. Other candidate attempts to read detail report (should get 404/403)
        self.client.force_authenticate(user=self.other_candidate)
        detail_url = reverse('evaluation_detail', args=[self.completed_session.id])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Admin retrieves candidate detail report successfully
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['overall_evaluation']['overall_score'], 81)

    def test_score_boundaries_validation(self):
        self.client.force_authenticate(user=self.admin)
        # Create evaluation
        self.client.post(self.generate_url, {'interview_id': self.completed_session.id}, format='json')

        technical_url = reverse('evaluation_technical', args=[self.completed_session.id])
        
        # Validate score validation boundaries
        response = self.client.put(technical_url, {'technical_score': 150}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(technical_url, {'technical_score': -10}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Valid score check
        response = self.client.put(technical_url, {'technical_score': 95}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['technical_score'], 95)

        # Check history audit entry written by signal
        evaluation = InterviewEvaluation.objects.get(interview=self.completed_session)
        self.assertTrue(EvaluationHistory.objects.filter(evaluation=evaluation, action="Technical Score Updated").exists())

    def test_suggestions_and_resources_crud(self):
        self.client.force_authenticate(user=self.candidate)
        self.client.post(self.generate_url, {'interview_id': self.completed_session.id}, format='json')
        evaluation = InterviewEvaluation.objects.get(interview=self.completed_session)

        # List suggestions
        suggestions_url = reverse('evaluation_suggestions_list', args=[self.completed_session.id])
        response = self.client.get(suggestions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

        # Create suggestion
        response = self.client.post(suggestions_url, {
            'category': 'System Design',
            'title': 'Learn Load Balancing',
            'description': 'Understand round-robin and hashing load balancing methods.',
            'priority': PRIORITY_HIGH
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sug_id = response.data['data']['id']

        # Update suggestion
        sug_detail_url = reverse('suggestion_detail', args=[sug_id])
        response = self.client.put(sug_detail_url, {
            'priority': PRIORITY_CRITICAL
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ImprovementSuggestion.objects.get(pk=sug_id).priority, PRIORITY_CRITICAL)

        # Delete suggestion
        response = self.client.delete(sug_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ImprovementSuggestion.objects.filter(pk=sug_id).exists())

    def test_export_report_pdf(self):
        self.client.force_authenticate(user=self.candidate)
        self.client.post(self.generate_url, {'interview_id': self.completed_session.id}, format='json')

        export_url = reverse('evaluation_export', args=[self.completed_session.id])
        response = self.client.get(export_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
