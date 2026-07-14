from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Category, ChatSession, ChatMessage, KnowledgeBase, Feedback, AdminAnalytics
from .services import normalize_text, find_best_match, find_local_answer, ChatbotService

User = get_user_model()

class ChatbotSystemTests(APITestCase):
    """
    Comprehensive test suite validating text matching logic, local DB lookups, 
    AI fallback triggers, REST API routing, and security controls.
    """

    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
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

        # Create Category
        self.category = Category.objects.create(
            name="General",
            description="General career queries"
        )

        # Create KnowledgeBase entries
        self.kb_entry = KnowledgeBase.objects.create(
            title="HR Interview Prep",
            category=self.category,
            question="How do I prepare for HR interview?",
            answer="Focus on standard behavioral questions, salary benchmarks, and STAR methodology.",
            keywords="hr, interview, behavioral",
            synonyms="hr round, human resources",
            priority=5,
            difficulty="Easy",
            tags="hr, career, softskills"
        )

        # REST API URLs
        self.send_msg_url = reverse('chat_send_message')
        self.history_url = reverse('chat_history')
        self.sessions_url = reverse('chat_sessions')
        self.session_create_url = reverse('chat_session_create')
        self.feedback_url = reverse('chat_feedback')
        self.categories_url = reverse('chat_categories')

    def test_text_normalization_helpers(self):
        text = "How do I prepare for HR interview???"
        normalized = normalize_text(text)
        self.assertEqual(normalized, "how do i prepare for hr interview")

    def test_similarity_matching_exact_and_synonym(self):
        # 1. Exact match query
        entry, score = find_best_match("prepare for HR interview")
        self.assertEqual(entry.id, self.kb_entry.id)
        self.assertTrue(score >= 0.5)

        # 2. Synonym match query
        entry_syn, score_syn = find_best_match("tell me about the HR round")
        self.assertEqual(entry_syn.id, self.kb_entry.id)
        self.assertTrue(score_syn >= 0.5)

    def test_local_vs_ai_fallback_answering(self):
        # Local lookup hit
        ans, priority, score, source, entry = find_local_answer("How do I prepare for HR interview?")
        self.assertIsNotNone(ans)
        self.assertEqual(source, 'LOCAL')

        # Local lookup miss (no match above threshold)
        ans_miss, priority_miss, score_miss, source_miss, entry_miss = find_local_answer("What is cellular biology?")
        self.assertNull = ans_miss
        self.assertIsNone(ans_miss)

    def test_sessions_rest_api_lifecycle(self):
        self.client.force_authenticate(user=self.user)

        # 1. Create session
        response = self.client.post(self.session_create_url, {"session_title": "My Test Session"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['session_title'], "My Test Session")
        session_id = response.data['data']['id']

        # 2. List sessions
        response = self.client.get(self.sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)

        # 3. Soft delete session
        delete_url = reverse('chat_session_delete', args=[session_id])
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify soft deleted sessions are excluded
        response = self.client.get(self.sessions_url)
        self.assertEqual(len(response.data['data']), 0)

    def test_send_message_local_lookup(self):
        self.client.force_authenticate(user=self.user)
        
        # Create session
        sess = ChatSession.objects.create(user=self.user, session_title="Test")

        # Send query matching local answer
        response = self.client.post(self.send_msg_url, {
            "session_id": sess.id,
            "message": "prepare for HR interview"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['response_source'], 'LOCAL')
        self.assertTrue("Focus on standard behavioral questions" in response.data['data']['message'])

        # Verify query hit logged in AdminAnalytics
        self.assertTrue(AdminAnalytics.objects.filter(was_matched=True, response_source='LOCAL').exists())

    def test_feedback_submission(self):
        self.client.force_authenticate(user=self.user)
        sess = ChatSession.objects.create(user=self.user, session_title="Test")
        
        msg = ChatMessage.objects.create(
            session=sess,
            sender='BOT',
            message="Test Answer",
            response_source='LOCAL'
        )

        response = self.client.post(self.feedback_url, {
            "message_id": msg.id,
            "rating": 5,
            "comment": "Very helpful!"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Feedback.objects.filter(message=msg, rating=5).exists())

    def test_admin_crud_knowledge_authorization(self):
        self.client.force_authenticate(user=self.user)
        knowledge_list_url = reverse('chatbot-knowledge-list')

        # Regular candidates should be denied access to knowledge configuration APIs
        response = self.client.get(knowledge_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin user should be allowed access
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(knowledge_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
