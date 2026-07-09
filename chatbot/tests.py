from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import (
    ChatSession,
    ChatMessage,
    PromptTemplate,
    ChatFeedback,
    ChatBookmark,
    ChatHistory
)
from .constants import STATUS_ACTIVE, STATUS_ARCHIVED, STATUS_DELETED

User = get_user_model()

class ChatbotModuleTests(APITestCase):
    """
    Unit test suite covering conversational chat sessions lifecycle, soft deletions,
    message sending, feedbacks ratings, bookmarks, and security boundaries checks.
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

        # Create pre-seeded prompts templates
        self.prompt = PromptTemplate.objects.create(
            name='Coding Mentor',
            category='Coding',
            system_prompt='You are an expert coding coach.',
            is_active=True
        )

        # URL paths
        self.start_url = reverse('chatbot_start_session')
        self.current_url = reverse('chatbot_current_session')
        self.sessions_list_url = reverse('chatbot_sessions_list')
        self.send_msg_url = reverse('chatbot_send_message')
        self.feedback_url = reverse('chatbot_feedback')
        self.bookmarks_url = reverse('chatbot-bookmark-list')
        self.prompts_list_url = reverse('chatbot-prompt-list')

    def test_session_creation_list_and_current(self):
        self.client.force_authenticate(user=self.candidate)

        # Start Chat Session
        response = self.client.post(self.start_url, {'conversation_type': 'Coding'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        session_id = response.data['data']['id']
        session = ChatSession.objects.get(pk=session_id)
        self.assertEqual(session.conversation_type, 'Coding')
        self.assertEqual(session.status, STATUS_ACTIVE)

        # Get Current Session
        response = self.client.get(self.current_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], session_id)

        # List Sessions
        response = self.client.get(self.sessions_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_session_rename_archive_and_soft_delete(self):
        self.client.force_authenticate(user=self.candidate)
        
        # Start session
        response = self.client.post(self.start_url, {'conversation_type': 'Coding'}, format='json')
        session_id = response.data['data']['id']

        detail_url = reverse('chatbot-session-detail', args=[session_id])
        archive_url = reverse('chatbot-session-archive', args=[session_id])

        # Rename Session
        response = self.client.put(detail_url, {'title': 'Updated Chat Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ChatSession.objects.get(pk=session_id).title, 'Updated Chat Title')

        # Archive Session
        response = self.client.post(archive_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ChatSession.objects.get(pk=session_id).status, STATUS_ARCHIVED)

        # Delete Session (Soft delete)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ChatSession.objects.get(pk=session_id).status, STATUS_DELETED)

        # Exclude deleted sessions from candidate lists
        response = self.client.get(self.sessions_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 0)

    def test_message_sending_and_timeline_retrieval(self):
        self.client.force_authenticate(user=self.candidate)

        # Start session
        response = self.client.post(self.start_url, {'conversation_type': 'Coding'}, format='json')
        session_id = response.data['data']['id']

        # Send Message (Stores user message and mock AI response)
        response = self.client.post(self.send_msg_url, {
            'session_id': session_id,
            'message': 'How does recursion work?'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        ai_msg_id = response.data['data']['id']

        # Check total messages count updated
        session = ChatSession.objects.get(pk=session_id)
        self.assertEqual(session.total_messages, 2)

        # Get Messages list
        messages_url = reverse('chatbot_messages_list', args=[session_id])
        response = self.client.get(messages_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

        # Verify history timeline logged
        history_url = reverse('chatbot_history_list', args=[session_id])
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['action'] == 'Message Sent' for item in response.data['data']))

    def test_rating_feedback_and_bookmarks(self):
        self.client.force_authenticate(user=self.candidate)

        # Start session
        response = self.client.post(self.start_url, {'conversation_type': 'Coding'}, format='json')
        session_id = response.data['data']['id']

        # Send Message
        response = self.client.post(self.send_msg_url, {
            'session_id': session_id,
            'message': 'Tell me about pointers.'
        }, format='json')
        ai_msg_id = response.data['data']['id']

        # 1. Feedback rating
        response = self.client.post(self.feedback_url, {
            'chat_message': ai_msg_id,
            'rating': 5,
            'comment': 'Stellar explanation!'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ChatFeedback.objects.filter(chat_message_id=ai_msg_id, rating=5).exists())

        # Rating boundary check (e.g. > 5 should fail)
        response = self.client.post(self.feedback_url, {
            'chat_message': ai_msg_id,
            'rating': 10
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Bookmarks
        response = self.client.post(self.bookmarks_url, {'chat_message': ai_msg_id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ChatBookmark.objects.filter(user=self.candidate, chat_message_id=ai_msg_id).exists())

        # List Bookmarks
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

    def test_security_access_controls(self):
        self.client.force_authenticate(user=self.candidate)

        # Start session
        response = self.client.post(self.start_url, {'conversation_type': 'Coding'}, format='json')
        session_id = response.data['data']['id']

        # Other candidate attempts to update it (should be 404)
        self.client.force_authenticate(user=self.other_candidate)
        detail_url = reverse('chatbot-session-detail', args=[session_id])
        
        response = self.client.put(detail_url, {'title': 'Hack attempt'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
