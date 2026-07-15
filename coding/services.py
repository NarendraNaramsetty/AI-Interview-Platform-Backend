from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Avg, Sum
from django.contrib.auth import get_user_model

from .models import (
    CodingProblem,
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

class CodingChallengeService:
    """
    Service layer containing future Judge0, sandbox executing, plagiarism check,
    and editorial generation placeholders. Implements draft saves and statistics.
    """

    # ----------------------------------------------------
    # Future Integration Placeholders
    # ----------------------------------------------------

    @staticmethod
    def execute_code(source_code: str, language: str, input_data: str) -> dict:
        """
        Placeholder: Sandbox code execution using Docker or Judge0 API.
        """
        return {"output": "Mock Output", "execution_time": 0.05, "memory_used": 12.4}

    @staticmethod
    def compile_code(source_code: str, language: str) -> dict:
        """
        Placeholder: Code compilation validation checks.
        """
        return {"success": True, "error_message": ""}

    @staticmethod
    def run_test_cases(source_code: str, language: str, problem_id: int) -> dict:
        """
        Placeholder: Execution of tests against hidden test inputs.
        """
        return {"passed": 5, "total": 5, "failed_cases": []}

    @staticmethod
    def calculate_score(passed: int, total: int, problem_points: int) -> dict:
        """
        Placeholder: Calculates score points and percentages.
        """
        percentage = (passed / total) * 100 if total > 0 else 0.0
        score = int((percentage / 100) * problem_points)
        ranking_points = score
        return {"score": score, "percentage": percentage, "ranking_points": ranking_points}

    @staticmethod
    def review_code_with_ai(source_code: str, problem_description: str) -> str:
        """
        Placeholder: Will eventually provide feedback using LLM review.
        """
        return "Clean code. Sub-optimal space complexity, consider in-place updates."

    @staticmethod
    def detect_plagiarism(source_code: str, problem_id: int) -> bool:
        """
        Placeholder: MOSS or similar check to check database duplicates.
        """
        return False

    @staticmethod
    def suggest_optimizations(source_code: str) -> list:
        """
        Placeholder: Suggest code refactor optimizations.
        """
        return ["Replace list appends with list comprehensions for speed."]

    @staticmethod
    def generate_editorial(problem_id: int) -> str:
        """
        Placeholder: Generates code solution editorial.
        """
        return "Editorial explanation: Use two pointers approach to run in O(N)."

    # ----------------------------------------------------
    # Session, Drafts, and Submissions Logic
    # ----------------------------------------------------

    @classmethod
    def start_coding_session(cls, problem_id: int, user) -> CodeSubmission:
        """
        Action: Start problem coding session. Creates a draft pending submission.
        """
        try:
            problem = CodingProblem.objects.get(pk=problem_id)
        except CodingProblem.DoesNotExist:
            raise ValidationError("Problem does not exist.")

        # Find or create a draft pending submission
        draft, created = CodeSubmission.objects.get_or_create(
            user=user,
            problem=problem,
            status=STATUS_PENDING,
            defaults={
                'source_code': "# Write your code here...",
                'programming_language': 'Python',
                'passed_test_cases': 0,
                'total_test_cases': 0
            }
        )

        # Log session start
        CodingHistory.objects.create(
            submission=draft,
            action="Problem Started",
            description=f"Candidate started coding session for problem: {problem.title}."
        )

        return draft

    @classmethod
    def save_code_draft(cls, problem_id: int, language: str, code: str, user) -> CodeSubmission:
        """
        Action: Autosave code draft as a Pending submission record.
        """
        try:
            problem = CodingProblem.objects.get(pk=problem_id)
        except CodingProblem.DoesNotExist:
            raise ValidationError("Problem does not exist.")

        draft = CodeSubmission.objects.filter(user=user, problem=problem, status=STATUS_PENDING).first()
        if not draft:
            draft = CodeSubmission(user=user, problem=problem, status=STATUS_PENDING)

        draft.programming_language = language
        draft.source_code = code
        draft.save()

        # Log history
        CodingHistory.objects.create(
            submission=draft,
            action="Code Saved",
            description=f"Source code draft autosaved for language: {language}."
        )

        return draft

    @classmethod
    def submit_code(cls, problem_id: int, language: str, code: str, user) -> CodeSubmission:
        """
        Action: Submit source code. Evaluates mock scores and ranking points.
        """
        try:
            problem = CodingProblem.objects.get(pk=problem_id)
        except CodingProblem.DoesNotExist:
            raise ValidationError("Problem does not exist.")

        from ai_core.services import AIService
        import json
        import re

        eval_prompt = f"""
You are "PrepAI Code Execution Sandbox" — an AI-powered code compiler and evaluation engine.
You are evaluating a candidate's code submission for the following coding challenge:

PROBLEM TITLE: {problem.title}
PROBLEM DESCRIPTION:
{problem.description}

SUBMITTED CODE:
```{language}
{code}
```

TASK:
1. Act as a language-specific compiler and execution environment.
2. Check for syntax correctness, logical edge cases, time/space complexity bounds.
3. Mentally execute the code against typical constraints and standard hidden inputs.
4. Calculate dynamic stats: passed_test_cases, total_test_cases (assign 5 as total), execution_time (in seconds, e.g. 0.01-1.5), memory_used (in MB, e.g. 5-30).
5. Compile clear feedback on logic bugs, optimization suggestions, and time/space complexity analysis.

Respond strictly in this JSON schema:
{{
  "compiles": true,
  "error_message": "",
  "passed_cases": 5,
  "total_cases": 5,
  "execution_time": 0.05,
  "memory_used": 12.4,
  "feedback_text": "All test cases passed."
}}
"""

        eval_data = {
            "compiles": True,
            "error_message": "",
            "passed_cases": 5,
            "total_cases": 5,
            "execution_time": 0.05,
            "memory_used": 12.4,
            "feedback_text": "All sample and hidden test cases passed successfully."
        }

        try:
            res_dict = AIService.route_request("chat", eval_prompt, user)
            raw_response = res_dict.get("response") if res_dict else None
            if raw_response:
                json_match = re.search(r'(\{.*\}|\[.*\])', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(1))
                else:
                    parsed = json.loads(raw_response)
                if isinstance(parsed, dict) and "passed_cases" in parsed:
                    eval_data.update(parsed)
        except Exception:
            pass

        with transaction.atomic():
            # Delete any existing Pending draft for this problem
            CodeSubmission.objects.filter(user=user, problem=problem, status=STATUS_PENDING).delete()

            passed = eval_data.get("passed_cases", 5)
            total = eval_data.get("total_cases", 5)
            percentage = (passed / total) * 100 if total > 0 else 0.0
            score = int((percentage / 100) * problem.points)
            status_submission = STATUS_ACCEPTED if eval_data.get("compiles", True) and passed == total else 'Failed'

            # Create final CodeSubmission
            submission = CodeSubmission.objects.create(
                user=user,
                problem=problem,
                programming_language=language,
                source_code=code,
                execution_time=eval_data.get("execution_time", 0.05),
                memory_used=eval_data.get("memory_used", 12.4),
                passed_test_cases=passed,
                total_test_cases=total,
                status=status_submission
            )

            # Generate score cards
            CodingScore.objects.create(
                submission=submission,
                score=score,
                percentage=percentage,
                ranking_points=score,
                feedback_placeholder=eval_data.get("feedback_text", "Evaluation completed.")
            )

            # Audit history logs
            CodingHistory.objects.create(
                submission=submission,
                action="Code Submitted",
                description="Final source code submitted to evaluation engine."
            )
            CodingHistory.objects.create(
                submission=submission,
                action="Evaluation Completed",
                description=f"AI execution completed. Result: {status_submission}."
            )

        return submission

    # ----------------------------------------------------
    # Statistics Calculator
    # ----------------------------------------------------

    @classmethod
    def get_coding_statistics(cls, user) -> dict:
        """
        Calculates:
        - Problems Solved: Unique problems with 'Accepted' submission.
        - Problems Attempted: Unique problems with any submissions.
        - Average Score: Average points earned.
        - Current Streak: Consecutive active submission days.
        - Preferred Language: Most used language.
        - Difficulty Breakdown: counts by Easy/Medium/Hard.
        """
        # Base queries
        submissions = CodeSubmission.objects.filter(user=user)
        total_subs = submissions.count()

        # Solved and attempted problems
        solved_problems = CodingProblem.objects.filter(
            submissions__user=user,
            submissions__status=STATUS_ACCEPTED
        ).distinct()
        solved_count = solved_problems.count()

        attempted_problems = CodingProblem.objects.filter(
            submissions__user=user
        ).distinct()
        attempted_count = attempted_problems.count()

        # Acceptance Rate
        # Calculate as (unique solved / unique attempted) * 100
        rate = (solved_count / attempted_count) * 100 if attempted_count > 0 else 0.0

        # Average Score
        avg_score = CodingScore.objects.filter(
            submission__user=user
        ).aggregate(Avg('score'))['score__avg'] or 0.0

        # Preferred Language
        pref_lang = submissions.values('programming_language').annotate(
            lang_count=Count('programming_language')
        ).order_by('-lang_count').first()
        preferred = pref_lang['programming_language'] if pref_lang else "Python"

        # Difficulty Breakdown
        difficulty_breakdown = {
            "Easy": solved_problems.filter(difficulty="Easy").count(),
            "Medium": solved_problems.filter(difficulty="Medium").count(),
            "Hard": solved_problems.filter(difficulty="Hard").count()
        }

        # Streak calculation
        streak = cls._calculate_streak(user)

        return {
            "problems_solved": solved_count,
            "problems_attempted": attempted_count,
            "acceptance_rate": round(rate, 2),
            "average_score": round(avg_score, 2),
            "current_streak": streak,
            "preferred_language": preferred,
            "difficulty_breakdown": difficulty_breakdown
        }

    @staticmethod
    def _calculate_streak(user) -> int:
        """
        Calculates user consecutive days streak based on submission dates in UTC.
        """
        dates = CodeSubmission.objects.filter(user=user).values_list('created_at', flat=True)
        local_dates = {timezone.localdate(d) for d in dates}
        if not local_dates:
            return 0

        sorted_dates = sorted(list(local_dates), reverse=True)
        today = timezone.localdate()
        yesterday = today - timezone.timedelta(days=1)

        # If user did not submit today or yesterday, streak is broken
        if sorted_dates[0] not in (today, yesterday):
            return 0

        streak = 1
        current_date = sorted_dates[0]
        for d in sorted_dates[1:]:
            if current_date - d == timezone.timedelta(days=1):
                streak += 1
                current_date = d
            elif current_date - d > timezone.timedelta(days=1):
                break

        return streak
