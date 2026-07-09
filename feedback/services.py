from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
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
    STATUS_COMPLETED,
    RATING_GOOD,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    RESOURCE_COURSE,
    RESOURCE_YOUTUBE
)

User = get_user_model()

class QuestionEvaluationService:
    """
    Business logic layer for evaluation processing. Includes placeholder methods
    for future Whisper and Ollama/Gemini AI models integration.
    """

    # ----------------------------------------------------
    # Future AI Integration Placeholders
    # ----------------------------------------------------

    @staticmethod
    def evaluate_technical_answer(answer_text: str, expected_answer: str = None) -> dict:
        """
        Placeholder: Will eventually evaluate technical answer correctness using Ollama/Gemini.
        """
        return {
            "technical_score": 85,
            "strengths": ["Correct description of python decorators decorator functions context."],
            "weaknesses": ["Missed explaining the closure retention mechanism."],
            "recommendations": ["Review closures and variables scoping in Python."]
        }

    @staticmethod
    def evaluate_hr_answer(answer_text: str) -> dict:
        """
        Placeholder: Will eventually analyze leadership, teamwork, and attitude scores using AI.
        """
        return {
            "confidence_score": 88,
            "professionalism_score": 85,
            "leadership_score": 75,
            "teamwork_score": 80,
            "adaptability_score": 82,
            "attitude_score": 85,
            "behavioral_feedback": "Exhibited professional vocabulary and highly structured responses."
        }

    @staticmethod
    def evaluate_communication(answer_text: str, audio_file=None) -> dict:
        """
        Placeholder: Will evaluate vocabulary, grammar, and fluency using transcript analysis.
        """
        return {
            "communication_score": 82,
            "grammar_score": 85,
            "fluency_score": 80,
            "vocabulary_score": 85,
            "clarity_score": 80
        }

    @staticmethod
    def calculate_confidence(audio_file=None, answer_text: str = None) -> int:
        """
        Placeholder: Calculates vocal and transcript confidence values.
        """
        return 88

    @staticmethod
    def calculate_pronunciation(audio_file) -> int:
        """
        Placeholder: Calculates pronunciation score from Whisper/Audio waveforms.
        """
        return 82

    @staticmethod
    def generate_learning_plan(evaluation_instance: InterviewEvaluation) -> str:
        """
        Placeholder: Generates next learning roadmap based on technical strengths and weaknesses.
        """
        return "Phase 1: Advanced Algorithms (1 week)\nPhase 2: Database Indexing & System Design (1 week)\nPhase 3: Mock Interviews (3 days)"

    @staticmethod
    def recommend_resources(evaluation_instance: InterviewEvaluation) -> list:
        """
        Placeholder: Recommends study assets matching weak points.
        """
        return [
            {
                "title": "Advanced Python Algorithms",
                "type": RESOURCE_COURSE,
                "url": "https://www.coursera.org/learn/algorithms",
                "description": "Comprehensive course covering advanced algorithms and data structures."
            },
            {
                "title": "System Design Indexing Guide",
                "type": RESOURCE_YOUTUBE,
                "url": "https://www.youtube.com/watch?v=indexing",
                "description": "Excellent video explanation of database indexing structures and strategies."
            }
        ]

    @staticmethod
    def generate_final_feedback(evaluation_instance: InterviewEvaluation) -> str:
        """
        Placeholder: Generates a human-like summary feedback string.
        """
        return "Strong performance across both technical and behavioral questions. Focus on refining database indexing concepts and practicing coding exercises to prepare for hard-level rounds."

    # ----------------------------------------------------
    # Evaluation Generation Logic
    # ----------------------------------------------------

    @classmethod
    def generate_evaluation_for_interview(cls, interview_id: int, user) -> InterviewEvaluation:
        """
        Generates standard feedback placeholders upon interview completions.
        - Validates session existence.
        - Validates completeness (Completed).
        - Validates user ownership.
        """
        # 1. Validate Interview Session
        try:
            session = InterviewSession.objects.all_with_deleted().get(pk=interview_id)
        except InterviewSession.DoesNotExist:
            raise ValidationError("Interview session does not exist.")

        # Check soft-deleted
        if session.deleted_at is not None:
            raise ValidationError("Cannot evaluate a deleted interview session.")

        # 2. Check Completeness
        if session.status != 'Completed':
            raise ValidationError("Cannot evaluate an incomplete interview session. Please finish the session first.")

        # 3. Verify Ownership (normal users can only evaluate their own, admins can bypass)
        if not user.is_staff and session.user != user:
            raise ValidationError("You do not have permission to access or generate evaluations for this session.")

        # If evaluation already exists, return it to prevent duplicate records
        existing_eval = InterviewEvaluation.objects.filter(interview=session).first()
        if existing_eval:
            return existing_eval

        # Generate database records inside atomic transaction
        with transaction.atomic():
            evaluation = InterviewEvaluation.objects.create(
                interview=session,
                user=session.user,
                evaluation_status=STATUS_COMPLETED,
                evaluated_at=timezone.now()
            )

            # Generate Technical Placeholder
            TechnicalEvaluation.objects.create(
                evaluation=evaluation,
                technical_score=78,
                coding_score=80,
                problem_solving_score=75,
                database_score=70,
                algorithm_score=85,
                explanation_quality=80,
                strengths=[
                    "Solid grasp of Python decorators syntax.",
                    "Clear explanation of time complexity requirements."
                ],
                weaknesses=[
                    "Missed closure variable binding details.",
                    "Database query optimization example was incomplete."
                ],
                recommendations=[
                    "Review closures scoping rules.",
                    "Practice indexes queries on larger tables."
                ]
            )

            # Generate Communication Placeholder
            CommunicationEvaluation.objects.create(
                evaluation=evaluation,
                communication_score=82,
                grammar_score=85,
                fluency_score=80,
                vocabulary_score=85,
                clarity_score=80,
                pronunciation_score_placeholder=75,
                confidence_score_placeholder=85
            )

            # Generate HR Placeholder
            HRBehaviorEvaluation.objects.create(
                evaluation=evaluation,
                confidence_score=88,
                professionalism_score=85,
                leadership_score=75,
                teamwork_score=80,
                adaptability_score=82,
                attitude_score=85,
                behavioral_feedback="Exhibited positive tone, active listening, and structured star-method answers."
            )

            # Generate Overall Placeholder
            OverallEvaluation.objects.create(
                evaluation=evaluation,
                overall_score=81,
                overall_rating=RATING_GOOD,
                recommendation="Recommended to proceed to the next technical round.",
                final_feedback=cls.generate_final_feedback(evaluation),
                next_learning_plan=cls.generate_learning_plan(evaluation)
            )

            # Generate Suggestions
            ImprovementSuggestion.objects.create(
                evaluation=evaluation,
                category="Database",
                title="Refine Database Normalization",
                description="Review 3NF database designs and normal forms details to design optimal relational databases.",
                priority=PRIORITY_CRITICAL
            )
            ImprovementSuggestion.objects.create(
                evaluation=evaluation,
                category="Algorithms",
                title="Edge Case Constraints Handling",
                description="Consider boundaries limits, null inputs, and integer overflow checks when solving algorithm problems.",
                priority=PRIORITY_HIGH
            )

            # Generate Resources
            resources = cls.recommend_resources(evaluation)
            for res in resources:
                RecommendedResource.objects.create(
                    evaluation=evaluation,
                    title=res['title'],
                    type=res['type'],
                    url=res['url'],
                    description=res['description']
                )

            # Log Initial History Log
            EvaluationHistory.objects.create(
                evaluation=evaluation,
                action="Evaluation Created",
                description="Placeholder scorecards, suggestions, and learning plans populated successfully."
            )

        return evaluation
