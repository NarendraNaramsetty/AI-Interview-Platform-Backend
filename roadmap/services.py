from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Avg
from django.contrib.auth import get_user_model

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
    STATUS_NOT_STARTED
)

User = get_user_model()

class RoadmapService:
    """
    Service layer containing future Ollama/Gemini, Qdrant/RAG, and skill gap analysis placeholders.
    Implements roadmap initiation, progress recalculation, streaks calculation, and pause/resume logic.
    """

    # ----------------------------------------------------
    # Future AI recommendation placeholders
    # ----------------------------------------------------

    @staticmethod
    def generate_personalized_roadmap(user_profile_data: dict, career_path_id: int) -> dict:
        """
        Placeholder: Will generate AI roadmaps using Gemini model APIs.
        """
        return {"roadmap_title": "AI Generated Roadmap", "modules": []}

    @staticmethod
    def recommend_next_module(user_roadmap_id: int) -> dict:
        """
        Placeholder: Recommends next module based on current progress.
        """
        return {"module_id": None, "reason": "Next chronological module."}

    @staticmethod
    def recommend_resources(module_id: int) -> list:
        """
        Placeholder: RAG resource lookup using sentence embeddings.
        """
        return []

    @staticmethod
    def predict_completion_time(user_roadmap_id: int) -> dict:
        """
        Placeholder: Predictive completion rate tracking.
        """
        return {"estimated_hours": 24, "confidence": 0.85}

    @staticmethod
    def recommend_projects(user_roadmap_id: int) -> list:
        """
        Placeholder: Recommends hands-on coding portfolio items.
        """
        return []

    @staticmethod
    def analyze_skill_gap(user_profile_id: int, target_job_role: str) -> dict:
        """
        Placeholder: Analyzes candidate resume vs job requirements gaps.
        """
        return {"missing_skills": [], "match_percentage": 75.0}

    # ----------------------------------------------------
    # Core Roadmap Workflows
    # ----------------------------------------------------

    @classmethod
    def start_roadmap(cls, roadmap_id: int, user) -> UserRoadmap:
        """
        Action: Start a roadmap. Creates a UserRoadmap tracking state.
        """
        try:
            roadmap = Roadmap.objects.get(pk=roadmap_id)
        except Roadmap.DoesNotExist:
            raise ValidationError("Roadmap does not exist.")

        # Check if already started
        existing = UserRoadmap.objects.filter(user=user, roadmap=roadmap).first()
        if existing:
            # If paused or completed, we return it. If not started, set to In Progress.
            if existing.status == STATUS_NOT_STARTED:
                existing.status = STATUS_IN_PROGRESS
                existing.save()
            return existing

        with transaction.atomic():
            first_module = roadmap.modules.order_by('module_order').first()
            
            user_roadmap = UserRoadmap.objects.create(
                user=user,
                roadmap=roadmap,
                status=STATUS_IN_PROGRESS,
                current_module=first_module,
                progress_percentage=0.0,
                completed_modules=0
            )

            # Pre-populate ModuleProgress items for all roadmap modules
            modules = roadmap.modules.all()
            for module in modules:
                ModuleProgress.objects.create(
                    user_roadmap=user_roadmap,
                    roadmap_module=module,
                    is_completed=False
                )

        return user_roadmap

    @classmethod
    def update_module_progress(cls, user_roadmap_id: int, module_id: int, is_completed: bool, notes: str, user) -> UserRoadmap:
        """
        Action: Update module completion details and recalculate roadmap percentages.
        """
        try:
            user_roadmap = UserRoadmap.objects.get(pk=user_roadmap_id, user=user)
        except UserRoadmap.DoesNotExist:
            raise ValidationError("User roadmap not found.")

        try:
            module = RoadmapModule.objects.get(pk=module_id, roadmap=user_roadmap.roadmap)
        except RoadmapModule.DoesNotExist:
            raise ValidationError("Roadmap module is not part of this roadmap.")

        with transaction.atomic():
            # Update individual module completion details
            progress, created = ModuleProgress.objects.get_or_create(
                user_roadmap=user_roadmap,
                roadmap_module=module
            )
            progress.is_completed = is_completed
            progress.notes = notes
            if is_completed:
                progress.completion_date = timezone.now()
            else:
                progress.completion_date = None
            progress.save()

            # Recalculate UserRoadmap metrics
            total_modules = user_roadmap.roadmap.modules.count()
            completed_count = ModuleProgress.objects.filter(
                user_roadmap=user_roadmap,
                is_completed=True
            ).count()

            user_roadmap.completed_modules = completed_count
            if total_modules > 0:
                user_roadmap.progress_percentage = round((completed_count / total_modules) * 100, 2)
            else:
                user_roadmap.progress_percentage = 0.0

            # Update statuses
            if user_roadmap.progress_percentage >= 100.0:
                user_roadmap.status = STATUS_COMPLETED
                user_roadmap.completed_at = timezone.now()
                user_roadmap.current_module = None
            else:
                # If completed previously and modules unchecked, set back to In Progress
                if user_roadmap.status == STATUS_COMPLETED:
                    user_roadmap.status = STATUS_IN_PROGRESS
                    user_roadmap.completed_at = None

                # Automatically update current module to next uncompleted module chronologically
                next_uncompleted = user_roadmap.roadmap.modules.filter(
                    progresses__user_roadmap=user_roadmap,
                    progresses__is_completed=False
                ).order_by('module_order').first()
                user_roadmap.current_module = next_uncompleted

            user_roadmap.save()

        return user_roadmap

    @classmethod
    def pause_roadmap(cls, roadmap_id: int, user) -> UserRoadmap:
        """
        Action: Pauses active roadmap.
        """
        try:
            user_roadmap = UserRoadmap.objects.get(roadmap_id=roadmap_id, user=user)
        except UserRoadmap.DoesNotExist:
            raise ValidationError("Active roadmap subscription not found.")

        user_roadmap.status = STATUS_PAUSED
        user_roadmap.save()
        return user_roadmap

    @classmethod
    def resume_roadmap(cls, roadmap_id: int, user) -> UserRoadmap:
        """
        Action: Resumes paused roadmap.
        """
        try:
            user_roadmap = UserRoadmap.objects.get(roadmap_id=roadmap_id, user=user)
        except UserRoadmap.DoesNotExist:
            raise ValidationError("Roadmap subscription not found.")

        user_roadmap.status = STATUS_IN_PROGRESS
        user_roadmap.save()
        return user_roadmap

    # ----------------------------------------------------
    # Statistics calculations
    # ----------------------------------------------------

    @classmethod
    def get_roadmap_statistics(cls, user) -> dict:
        """
        Aggregates:
        - Hours Learned: Sum of estimated hours of completed modules.
        - Completed Modules: Total count of completed modules.
        - Completed Roadmaps: Count of roadmaps completed.
        - Learning Streak: Consecutive days active.
        - Completion Rate: (completed roadmaps / total started) * 100.
        """
        # Completed modules count
        completed_modules_qs = ModuleProgress.objects.filter(
            user_roadmap__user=user,
            is_completed=True
        )
        completed_modules_count = completed_modules_qs.count()

        # Hours learned
        hours_learned = completed_modules_qs.aggregate(
            total_hours=Sum('roadmap_module__estimated_hours')
        )['total_hours'] or 0

        # Completed roadmaps
        roadmaps_qs = UserRoadmap.objects.filter(user=user)
        total_roadmaps = roadmaps_qs.count()
        completed_roadmaps_count = roadmaps_qs.filter(status=STATUS_COMPLETED).count()

        # Completion Rate
        rate = (completed_roadmaps_count / total_roadmaps) * 100 if total_roadmaps > 0 else 0.0

        # Streak calculation
        streak = cls._calculate_learning_streak(user)

        return {
            "hours_learned": hours_learned,
            "completed_modules": completed_modules_count,
            "completed_roadmaps": completed_roadmaps_count,
            "learning_streak": streak,
            "completion_rate": round(rate, 2)
        }

    @staticmethod
    def _calculate_learning_streak(user) -> int:
        """
        Calculates consecutive learning days based on ModuleProgress completion dates.
        """
        dates = ModuleProgress.objects.filter(
            user_roadmap__user=user,
            is_completed=True,
            completion_date__isnull=False
        ).values_list('completion_date', flat=True)
        local_dates = {timezone.localdate(d) for d in dates}
        if not local_dates:
            return 0

        sorted_dates = sorted(list(local_dates), reverse=True)
        today = timezone.localdate()
        yesterday = today - timezone.timedelta(days=1)

        # If user did not complete anything today or yesterday, streak is 0
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
