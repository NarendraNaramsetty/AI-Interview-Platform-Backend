import os
import time
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from interviews.models import InterviewSession
from interviews.services import InterviewService
from questions.models import InterviewQuestion as BankQuestion, QuestionCategory, Topic
from nlp.utils.circuit_breaker import CircuitBreaker
from nlp.utils.ai_runner import execute_ai_call_with_retry
from nlp.utils.exceptions import AIException, AITimeoutError, AIParsingError, AIProviderError
from nlp.utils.code_challenge_generator import CodeChallengeGenerator

User = get_user_model()

class AIFallbackTestCase(TestCase):
    def setUp(self):
        # Reset Circuit Breaker states before each test run
        CircuitBreaker.reset_all()
        
        self.user = User.objects.create_user(
            username="testcandidate",
            email="testcandidate@example.com",
            password="securepassword"
        )
        self.session = InterviewSession.objects.create(
            user=self.user,
            title="Mock Mock Test",
            target_role="Software Engineer",
            target_company="Google",
            interview_type="Technical",
            difficulty="Medium",
            interview_mode="Text",
            language="Python",
            total_questions=2,
            duration_minutes=30
        )
        
        # Prepare categories and topics for Tier 2 Database Bank setup
        self.category = QuestionCategory.objects.create(name="Technical")
        self.topic = Topic.objects.create(name="Python", category=self.category)

    @patch("nlp.utils.ai_runner.AIService.route_request")
    def test_tier_1_success(self, mock_route):
        """Tier 1 Success: AI returns valid JSON questions, saved to session DB."""
        ai_response = [
            {
                "question_text": "Describe the difference between Python lists and tuples in terms of memory layout.",
                "topic": "Python",
                "category": "Technical",
                "expected_answer_placeholder": "Lists are mutable/dynamic; tuples are immutable/fixed size."
            },
            {
                "question_text": "What is the global interpreter lock (GIL) and how does it impact concurrency?",
                "topic": "Python",
                "category": "Technical",
                "expected_answer_placeholder": "Prevents multiple threads from executing Python bytecodes at once."
            }
        ]
        mock_route.return_value = {"response": json.dumps(ai_response)}
        
        questions = InterviewService.generate_questions(self.session)
        
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0].source, "AI_Core")
        self.assertEqual(questions[0].question_text, ai_response[0]["question_text"])
        self.assertEqual(mock_route.call_count, 1)

    @patch("nlp.utils.ai_runner.AIService.route_request")
    def test_tier_1_timeout_falls_to_tier_2(self, mock_route):
        """Tier 1 Timeout: Falls back to database question bank (Tier 2)."""
        # Induce a timeout exception
        mock_route.side_effect = TimeoutError("Request timed out")
        
        # Seed matching database questions for Tier 2
        BankQuestion.objects.create(
            question="DB Bank Python Question 1?",
            difficulty="Medium",
            expected_duration=10,
            category=self.category,
            topic=self.topic,
            is_active=True
        )
        BankQuestion.objects.create(
            question="DB Bank Python Question 2?",
            difficulty="Medium",
            expected_duration=10,
            category=self.category,
            topic=self.topic,
            is_active=True
        )
        
        questions = InterviewService.generate_questions(self.session)
        
        # Should call once (Attempt 1), and then exactly once more (Retry with 5s timeout)
        self.assertEqual(mock_route.call_count, 2)
        
        # Assert returned questions are loaded from database (Tier 2)
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0].source, "Database")
        self.assertTrue(questions[0].question_text.startswith("DB Bank Python"))

    @patch("nlp.utils.ai_runner.AIService.route_request")
    def test_tier_1_timeout_tier_2_no_match_falls_to_tier_3(self, mock_route):
        """Tier 1 Timeout and Tier 2 No DB Matches: Falls back to hardcoded prompts (Tier 3)."""
        mock_route.side_effect = TimeoutError("Connection timed out")
        
        # Clear out any potential database questions to force no db match
        BankQuestion.objects.all().delete()
        
        questions = InterviewService.generate_questions(self.session)
        
        # Assert returned questions are loaded from hardcoded default prompts (Tier 3)
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0].source, "Database")
        self.assertTrue("Introduce yourself" in questions[0].question_text or "culture" in questions[0].question_text or "culture" in questions[1].question_text)

    @patch("nlp.utils.ai_runner.AIService.route_request")
    def test_tier_1_parse_error_falls_to_tier_2(self, mock_route):
        """Tier 1 Parse Error: Returns invalid JSON, falls back to DB."""
        mock_route.return_value = {"response": "This is raw unformatted text instead of JSON!"}
        
        BankQuestion.objects.create(
            question="DB Bank Python Question?",
            difficulty="Medium",
            expected_duration=10,
            category=self.category,
            topic=self.topic,
            is_active=True
        )
        
        questions = InterviewService.generate_questions(self.session)
        
        self.assertEqual(mock_route.call_count, 1) # Parse error shouldn't retry (only timeout retries)
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0].source, "Database")

    @patch("nlp.utils.circuit_breaker.AI_BREAKER_FAILURE_THRESHOLD", 2)
    @patch("nlp.utils.ai_runner.AIService.route_request")
    def test_circuit_breaker_trips_and_skips_tier_1(self, mock_route):
        """Circuit Breaker: Trips after threshold failures and shunts directly to fallback."""
        mock_route.side_effect = TimeoutError("Mock network timeout")
        
        # Trigger 2 timeout failures (matching mock threshold of 2)
        with self.assertRaises(AIException):
            execute_ai_call_with_retry(
                "chat", "Prompt", self.user, "interview", "123", "456", 
                {"difficulty": "medium", "company": "Google", "mode": "Technical"},
                lambda x: json.loads(x)
            )
            
        with self.assertRaises(AIException):
            execute_ai_call_with_retry(
                "chat", "Prompt", self.user, "interview", "123", "456", 
                {"difficulty": "medium", "company": "Google", "mode": "Technical"},
                lambda x: json.loads(x)
            )
            
        # Breaker should now be OPEN.
        breaker = CircuitBreaker("Gemini")
        self.assertEqual(breaker.state, "OPEN")
        
        # Verify call count is 4 (2 attempts per run)
        self.assertEqual(mock_route.call_count, 4)
        
        # Next call should fail immediately with AIProviderError (open breaker) WITHOUT incrementing route_request
        with self.assertRaises(AIProviderError) as context:
            execute_ai_call_with_retry(
                "chat", "Prompt", self.user, "interview", "123", "456", 
                {"difficulty": "medium", "company": "Google", "mode": "Technical"},
                lambda x: json.loads(x)
            )
        
        self.assertTrue("Circuit breaker is open" in str(context.exception))
        self.assertEqual(mock_route.call_count, 4) # Should not have called provider again

    @patch("nlp.utils.circuit_breaker.AI_BREAKER_FAILURE_THRESHOLD", 1)
    @patch("nlp.utils.circuit_breaker.AI_BREAKER_COOLDOWN_SECONDS", 1)
    @patch("nlp.utils.ai_runner.AIService.route_request")
    def test_circuit_breaker_half_open_trial_resets(self, mock_route):
        """Circuit Breaker: Cooldown expiration allows trial request and resets to CLOSED on success."""
        mock_route.side_effect = TimeoutError("Timed out")
        
        # 1. Induce one failure to trip the breaker (threshold = 1)
        with self.assertRaises(AIException):
            execute_ai_call_with_retry(
                "chat", "Prompt", self.user, "interview", "123", "456", 
                {"difficulty": "medium", "company": "Google", "mode": "Technical"},
                lambda x: json.loads(x)
            )
        
        breaker = CircuitBreaker("Gemini")
        self.assertEqual(breaker.state, "OPEN")
        
        # 2. Wait for cooldown to expire
        time.sleep(1.1)
        
        # 3. Allow next request (which will transition to HALF-OPEN) and succeed
        mock_route.side_effect = None
        mock_route.return_value = {"response": '{"ok": true}'}
        
        result = execute_ai_call_with_retry(
            "chat", "Prompt", self.user, "interview", "123", "456", 
            {"difficulty": "medium", "company": "Google", "mode": "Technical"},
            lambda x: json.loads(x)
        )
        
        # Breaker should now have transitioned back to CLOSED
        self.assertEqual(breaker.state, "CLOSED")
        self.assertTrue(result["ok"])
