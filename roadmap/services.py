from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Avg
from django.contrib.auth import get_user_model
from typing import Optional, Dict, Any, List

from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder,
    RoadmapPathway,
    RoadmapMilestone
)
from .constants import (
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED,
    STATUS_PAUSED,
    STATUS_NOT_STARTED
)
from nlp.utils.roadmap_generator import generate_roadmap, calculate_total_hours

User = get_user_model()


class RoadmapService:
    """Service layer for roadmap operations."""

    @staticmethod
    @transaction.atomic
    def create_pathway_from_interest(
        user,
        interest_text: str,
        self_described_experience: Optional[str] = None,
        resume_context_summary: Optional[str] = None
    ) -> RoadmapPathway:
        """
        Generate and create a new roadmap pathway for a user.
        
        Args:
            user: The user creating the pathway
            interest_text: What user wants to learn/become
            self_described_experience: Optional background info
            resume_context_summary: Optional resume context
            
        Returns:
            RoadmapPathway instance with milestones
            
        Raises:
            ValueError: If LLM generation fails or schema validation fails
        """
        
        # Generate roadmap via LLM
        roadmap_data = generate_roadmap(
            user_interest_text=interest_text,
            self_described_experience=self_described_experience,
            resume_context_summary=resume_context_summary
        )
        
        # Create pathway
        pathway = RoadmapPathway.objects.create(
            user=user,
            user_interest_text=interest_text,
            pathway_title=roadmap_data['pathway_title'],
            inferred_starting_level=roadmap_data['inferred_starting_level'],
            inferred_level_reason=roadmap_data['inferred_level_reason'],
            overall_readiness_estimate_percent=roadmap_data['overall_readiness_estimate_percent'],
        )
        
        # Create milestones
        milestones = []
        for milestone_data in roadmap_data['milestones']:
            milestone = RoadmapMilestone.objects.create(
                pathway=pathway,
                milestone_number=milestone_data['milestone_number'],
                title=milestone_data['title'],
                difficulty_tag=milestone_data['difficulty_tag'],
                description=milestone_data['description'],
                why_it_matters=milestone_data['why_it_matters'],
                estimated_hours=milestone_data['estimated_hours'],
                key_topics=milestone_data['key_topics'],
            )
            milestones.append(milestone)
        
        return pathway
    
    @staticmethod
    def get_user_pathways(user, limit: Optional[int] = None) -> List[RoadmapPathway]:
        """Get all pathways for a user, optionally limited."""
        query = RoadmapPathway.objects.filter(user=user).order_by('-created_at')
        if limit:
            return list(query[:limit])
        return list(query)
    
    @staticmethod
    def get_pathway_with_milestones(pathway_id: int, user) -> Optional[RoadmapPathway]:
        """Get a specific pathway with all milestones (checks authorization)."""
        try:
            return RoadmapPathway.objects.get(id=pathway_id, user=user)
        except RoadmapPathway.DoesNotExist:
            return None
    
    @staticmethod
    def update_milestone_progress(
        milestone: RoadmapMilestone,
        progress_percent: Optional[int] = None,
        is_completed: Optional[bool] = None
    ) -> RoadmapMilestone:
        """
        Update milestone progress.
        
        Args:
            milestone: The milestone to update
            progress_percent: New progress (0-100)
            is_completed: Mark as completed
            
        Returns:
            Updated milestone
        """
        
        if progress_percent is not None:
            if not (0 <= progress_percent <= 100):
                raise ValidationError("Progress must be between 0 and 100")
            milestone.progress_percent = progress_percent
        
        if is_completed is not None:
            milestone.is_completed = is_completed
            if is_completed:
                milestone.progress_percent = 100
        
        milestone.save()
        return milestone
    
    @staticmethod
    def get_pathway_statistics(pathway: RoadmapPathway) -> Dict[str, Any]:
        """Get progress statistics for a pathway."""
        milestones = pathway.milestones.all()
        
        if not milestones.exists():
            return {
                'total_milestones': 0,
                'completed_milestones': 0,
                'overall_progress_percent': 0,
                'total_hours': 0,
                'average_milestone_progress': 0
            }
        
        completed_count = milestones.filter(is_completed=True).count()
        total_count = milestones.count()
        total_hours = sum(m.estimated_hours for m in milestones)
        avg_progress = sum(m.progress_percent for m in milestones) / total_count if total_count > 0 else 0
        
        return {
            'total_milestones': total_count,
            'completed_milestones': completed_count,
            'overall_progress_percent': round((completed_count / total_count * 100) if total_count > 0 else 0),
            'total_hours': total_hours,
            'average_milestone_progress': round(avg_progress)
        }
    
    @staticmethod
    def delete_pathway(pathway: RoadmapPathway) -> bool:
        """
        Delete a pathway and cascade delete milestones.
        
        Returns:
            True if deleted successfully
        """
        try:
            pathway_id = pathway.id
            pathway.delete()
            return True
        except Exception as e:
            raise ValueError(f"Failed to delete pathway: {str(e)}")




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
    def update_module_progress(cls, user_roadmap_id: int, module_id: int, is_completed: Optional[bool] = None, notes: Optional[str] = None, is_bookmarked: Optional[bool] = None, user=None) -> UserRoadmap:
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
            if is_completed is not None:
                progress.is_completed = is_completed
                if is_completed:
                    progress.completion_date = timezone.now()
                else:
                    progress.completion_date = None
            if is_bookmarked is not None:
                progress.is_bookmarked = is_bookmarked
            if notes is not None:
                progress.notes = notes
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


class RoadmapAnalyticsService:
    """Analytics for roadmap data."""
    
    @staticmethod
    def get_user_roadmap_summary(user) -> Dict[str, Any]:
        """Get summary stats for all user's roadmaps."""
        pathways = RoadmapPathway.objects.filter(user=user)
        
        total_pathways = pathways.count()
        total_milestones = sum(p.milestones.count() for p in pathways)
        total_hours = sum(
            sum(m.estimated_hours for m in p.milestones.all())
            for p in pathways
        )
        
        completed_pathways = sum(
            1 for p in pathways 
            if p.milestones.filter(is_completed=True).count() == p.milestones.count()
        )
        
        in_progress_pathways = total_pathways - completed_pathways
        
        return {
            'total_pathways': total_pathways,
            'in_progress_pathways': in_progress_pathways,
            'completed_pathways': completed_pathways,
            'total_milestones': total_milestones,
            'total_hours': total_hours,
        }
    
    @staticmethod
    def get_learning_difficulty_breakdown(user) -> Dict[str, int]:
        """Count pathways/milestones by difficulty level."""
        pathways = RoadmapPathway.objects.filter(user=user)
        
        breakdown = {
            'beginner': pathways.filter(inferred_starting_level='Beginner').count(),
            'intermediate': pathways.filter(inferred_starting_level='Intermediate').count(),
            'advanced': pathways.filter(inferred_starting_level='Advanced').count(),
        }
        
        return breakdown
    
    @staticmethod
    def get_average_readiness_progress(user) -> float:
        """Get average readiness percentage across all pathways."""
        pathways = RoadmapPathway.objects.filter(user=user)
        
        if not pathways.exists():
            return 0.0
        
        total_readiness = sum(p.overall_readiness_estimate_percent for p in pathways)
        return total_readiness / pathways.count()
    
    @staticmethod
    def get_most_recent_pathways(user, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recently created pathways."""
        pathways = RoadmapPathway.objects.filter(user=user).order_by('-created_at')[:limit]
        
        return [
            {
                'id': p.id,
                'title': p.pathway_title,
                'interest': p.user_interest_text,
                'level': p.inferred_starting_level,
                'readiness': p.overall_readiness_estimate_percent,
                'milestone_count': p.milestones.count(),
                'created_at': p.created_at.isoformat(),
            }
            for p in pathways
        ]
