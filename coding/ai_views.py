import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
# pyrefly: ignore [missing-import]
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import CodingSession, GeneratedQuestion, QuestionAttempt, LearningProgress, HintUsage
from .ai_services import AISandboxService
from resume.models import Resume

logger = logging.getLogger(__name__)

class GenerateAIQuestionView(APIView):
    """
    POST /api/ai/generate-question/
    Generates a personalized coding challenge based on preferences and resume context.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        use_resume = data.get('use_resume', False)
        
        resume_context = ""
        if use_resume:
            user_resume = Resume.objects.filter(user=request.user, deleted_at__isnull=True).first()
            if user_resume:
                resume_context = user_resume.resume_text[:2000] # Limit to first 2000 chars

        # Map frontend values to prompt builder parameters
        params = {
            "role": data.get('role', 'Backend Engineer'),
            "experience": data.get('experience', 'Mid-Level'),
            "programming_language": data.get('programming_language', 'python'),
            "difficulty": data.get('difficulty', 'Medium'),
            "company": data.get('company', 'Startup'),
            "focus_areas": data.get('focus_areas', []),
            "interview_goal": data.get('interview_goal', 'Practice'),
            "resume_context": resume_context
        }

        try:
            challenge = AISandboxService.generate_coding_challenge(params)
            
            # Save configuration session
            session = CodingSession.objects.create(
                user=request.user,
                practice_type=data.get('practice_type', 'Backend Development'),
                role=params['role'],
                tech_stack=data.get('tech_stack', []),
                company=params['company'],
                experience=params['experience'],
                difficulty=params['difficulty'],
                question_count=int(data.get('question_count', 5)),
                focus_areas=params['focus_areas'],
                interview_goal=params['interview_goal']
            )

            # Save generated problem detail
            question = GeneratedQuestion.objects.create(
                session=session,
                title=challenge.get('title', 'AI Personal Challenge'),
                description=challenge.get('description', 'Problem description payload'),
                difficulty=params['difficulty'],
                programming_language=params['programming_language'],
                starter_code=challenge.get('starter_code', ''),
                test_cases=challenge.get('test_cases', []),
                hints=challenge.get('hints', []),
                optimal_solution=challenge.get('optimal_solution', '')
            )

            return Response({
                "success": True,
                "session_id": session.id,
                "question_id": question.id,
                "question": {
                    "title": question.title,
                    "description": question.description,
                    "difficulty": question.difficulty,
                    "starter_code": question.starter_code,
                    "hints": question.hints,
                    "programming_language": question.programming_language,
                    "test_cases": question.test_cases
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to generate AI coding challenge: {str(e)}")
            return Response({
                "success": False,
                "message": f"Generation failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewAICodeView(APIView):
    """
    POST /api/ai/review-code/
    Reviews candidate code against AI evaluation parameters, saves scores, and streaks.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        question_id = data.get('question_id')
        source_code = data.get('source_code')
        lang = data.get('programming_language', 'python')
        run_status = data.get('status', 'Compiled')
        passed = int(data.get('passed_test_cases', 0))
        total = int(data.get('total_test_cases', 0))

        if not question_id or not source_code:
            return Response({
                "success": False,
                "message": "Missing required fields."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = GeneratedQuestion.objects.get(id=question_id)
        except GeneratedQuestion.DoesNotExist:
            return Response({
                "success": False,
                "message": "Generated question not found."
            }, status=status.HTTP_404_NOT_FOUND)

        attempt_data = {
            "title": question.title,
            "description": question.description,
            "source_code": source_code,
            "programming_language": lang,
            "status": run_status,
            "passed_test_cases": passed,
            "total_test_cases": total
        }

        try:
            ai_review = AISandboxService.review_user_code(attempt_data)
            score = int(ai_review.get('score', 80))

            # Record attempt
            attempt = QuestionAttempt.objects.create(
                user=request.user,
                question=question,
                source_code=source_code,
                programming_language=lang,
                passed_test_cases=passed,
                total_test_cases=total,
                status=run_status,
                score=score,
                ai_review=ai_review,
                follow_up_questions=ai_review.get('follow_up_questions', [])
            )

            # Update gamification/streak state
            progress, created = LearningProgress.objects.get_or_create(user=request.user)
            
            # Increment Solved count
            progress.problems_solved += 1
            progress.xp += score + 50  # Award XP
            progress.coins += 10       # Award Coins
            
            # Recalculate average score
            total_solved = progress.problems_solved
            progress.average_score = round(((progress.average_score * (total_solved - 1)) + score) / total_solved, 1)

            # Update language used list
            if lang not in progress.languages_used:
                progress.languages_used.append(lang)

            # Sync readiness score
            progress.readiness_score = min(max(50 + (total_solved * 2), 50), 100)

            # Manage streak
            progress.current_streak = max(progress.current_streak + 1, 1)
            progress.save()

            return Response({
                "success": True,
                "score": score,
                "correctness": ai_review.get('correctness', ''),
                "performance": ai_review.get('performance', ''),
                "code_quality": ai_review.get('code_quality', ''),
                "edge_cases": ai_review.get('edge_cases', ''),
                "alternative_solution": ai_review.get('alternative_solution', ''),
                "suggestions": ai_review.get('suggestions', []),
                "follow_up_questions": attempt.follow_up_questions,
                "gamification": {
                    "xp_gained": score + 50,
                    "coins_gained": 10,
                    "total_xp": progress.xp,
                    "streak": progress.current_streak
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to evaluate candidate code: {str(e)}")
            return Response({
                "success": False,
                "message": f"Review failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CodingLearningDashboardView(APIView):
    """
    GET /api/ai/coding-dashboard/
    Retrieves the aggregate stats for the personalized coding hub.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        progress, created = LearningProgress.objects.get_or_create(user=request.user)
        
        # Load recent attempts
        attempts = QuestionAttempt.objects.filter(user=request.user).order_by('-created_at')
        recent_history = []
        for att in attempts[:5]:
            recent_history.append({
                "id": att.id,
                "title": att.question.title,
                "score": att.score,
                "programming_language": att.programming_language,
                "date": att.created_at.strftime('%Y-%m-%d'),
                "status": att.status
            })

        return Response({
            "problems_solved": progress.problems_solved,
            "current_streak": progress.current_streak,
            "average_score": progress.average_score,
            "readiness_score": progress.readiness_score,
            "xp": progress.xp,
            "coins": progress.coins,
            "languages_used": progress.languages_used,
            "top_skills": progress.top_skills or ["APIs", "Data Structures"],
            "weak_skills": progress.weak_skills or ["Redis Caching", "System Complexity"],
            "recent_history": recent_history
        }, status=status.HTTP_200_OK)
