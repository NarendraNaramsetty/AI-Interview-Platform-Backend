from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from .models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewProgress,
    InterviewResult,
    InterviewTimeline
)
from .services import InterviewService
from .constants import STATUS_PAUSED, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_SCHEDULED

User = get_user_model()

class InterviewModuleTests(APITestCase):
    """
    Unit test suite covering the full lifecycle of mock interview prep sessions.
    """

    def setUp(self):
        # Create test users
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

        # Base endpoints
        self.start_url = reverse('interview_start')
        self.active_url = reverse('interview_current')
        self.history_url = reverse('interview_history')

    def test_start_interview_success(self):
        self.client.force_authenticate(user=self.user1)
        data = {
            'target_role': 'Python Developer',
            'target_company': 'Google',
            'interview_type': 'Technical',
            'difficulty': 'Medium',
            'interview_mode': 'Text',
            'language': 'English',
            'total_questions': 5,
            'duration_minutes': 45
        }
        response = self.client.post(self.start_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        session_id = response.data['data']['id']
        session = InterviewSession.objects.get(id=session_id)
        self.assertEqual(session.target_role, 'Python Developer')
        self.assertEqual(session.questions.count(), 5)
        self.assertEqual(session.status, STATUS_IN_PROGRESS)
        
        # Verify related records created automatically by signal/service
        self.assertIsNotNone(session.progress)
        self.assertEqual(session.progress.remaining_questions, 5)

    def test_get_current_active_interview(self):
        self.client.force_authenticate(user=self.user1)
        
        # Initially, no active interview
        response = self.client.get(self.active_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Start one
        session = InterviewService.start_interview(
            user=self.user1,
            target_role='Django Dev',
            target_company='Meta',
            interview_type='Technical',
            difficulty='Hard',
            interview_mode='Text',
            language='English',
            total_questions=3,
            duration_minutes=30
        )
        
        response = self.client.get(self.active_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], session.id)

    def test_pause_and_resume_interview(self):
        self.client.force_authenticate(user=self.user1)
        session = InterviewService.start_interview(
            user=self.user1,
            target_role='Django Dev',
            target_company='Meta',
            interview_type='Technical',
            difficulty='Hard',
            interview_mode='Text',
            language='English',
            total_questions=3,
            duration_minutes=30
        )

        pause_url = reverse('interview_pause', args=[session.id])
        resume_url = reverse('interview_resume', args=[session.id])

        # Pause
        response = self.client.post(pause_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, STATUS_PAUSED)

        # Resume
        response = self.client.post(resume_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, STATUS_IN_PROGRESS)

    def test_save_answer_and_flow_pointers(self):
        self.client.force_authenticate(user=self.user1)
        session = InterviewService.start_interview(
            user=self.user1,
            target_role='React Dev',
            target_company='Netflix',
            interview_type='Technical',
            difficulty='Medium',
            interview_mode='Text',
            language='English',
            total_questions=3,
            duration_minutes=30
        )

        first_question = session.questions.first()
        answer_url = reverse('interview_answer', args=[session.id])
        
        # Save Answer
        data = {
            'question_id': first_question.id,
            'answer_text': 'I have 3 years of React experience.',
            'answer_duration': 15
        }
        response = self.client.post(answer_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        session.refresh_from_db()
        # Answer count incremented
        self.assertEqual(session.answered_questions, 1)
        # Sequence index shifted to 1
        self.assertEqual(session.current_question_index, 1)
        self.assertAlmostEqual(session.progress.percentage_completed, 33.33, places=2)

        # Test Next and Previous pointer Views
        next_url = reverse('interview_next', args=[session.id])
        prev_url = reverse('interview_previous', args=[session.id])
        skip_url = reverse('interview_skip', args=[session.id])

        # Reset pointer back to 0
        session.current_question_index = 0
        session.save()

        # Next pointer test
        response = self.client.post(next_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.current_question_index, 1)

        # Prev pointer test
        response = self.client.post(prev_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.current_question_index, 0)

        # Skip pointer test
        response = self.client.post(skip_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.current_question_index, 1)
        # Verify skip timeline logged
        self.assertTrue(session.timeline_events.filter(action='Question Skipped').exists())

    def test_end_interview_generates_result(self):
        self.client.force_authenticate(user=self.user1)
        session = InterviewService.start_interview(
            user=self.user1,
            target_role='Flask Dev',
            target_company='Apple',
            interview_type='Technical',
            difficulty='Medium',
            interview_mode='Text',
            language='English',
            total_questions=3,
            duration_minutes=30
        )

        end_url = reverse('interview_end', args=[session.id])
        response = self.client.post(end_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        session.refresh_from_db()
        self.assertEqual(session.status, STATUS_COMPLETED)
        
        # Verify AI scores placeholder populated
        result = session.result
        self.assertEqual(result.status, 'Completed')
        self.assertEqual(result.overall_score, 83)
        self.assertIn('Flask', result.feedback_placeholder or '')

    def test_duplicate_session(self):
        self.client.force_authenticate(user=self.user1)
        session = InterviewService.start_interview(
            user=self.user1,
            target_role='Vue Dev',
            target_company='Amazon',
            interview_type='Technical',
            difficulty='Medium',
            interview_mode='Text',
            language='English',
            total_questions=3,
            duration_minutes=30
        )

        duplicate_url = reverse('interview_duplicate', args=[session.id])
        response = self.client.post(duplicate_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        duplicated_id = response.data['data']['id']
        duplicated_session = InterviewSession.objects.get(id=duplicated_id)
        self.assertEqual(duplicated_session.status, STATUS_SCHEDULED)
        self.assertEqual(duplicated_session.target_role, 'Vue Dev')
        # Check questions cloned
        self.assertEqual(duplicated_session.questions.count(), 3)

    def test_soft_delete_and_permissions(self):
        # Alice starts session
        session = InterviewService.start_interview(
            user=self.user1,
            target_role='Golang Dev',
            target_company='Uber',
            interview_type='Technical',
            difficulty='Medium',
            interview_mode='Text',
            language='English',
            total_questions=3,
            duration_minutes=30
        )

        # Bob tries to delete Alice's session
        self.client.force_authenticate(user=self.user2)
        detail_url = reverse('interview_detail', args=[session.id])
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Alice deletes her own session
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify soft deleted (hidden in active managers)
        self.assertEqual(InterviewSession.objects.filter(id=session.id).count(), 0)
        self.assertEqual(InterviewSession.objects.all_with_deleted().filter(id=session.id).count(), 1)
