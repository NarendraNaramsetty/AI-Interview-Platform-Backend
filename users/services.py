import os
from django.db import models
from .models import UserProfile, UserStatistics
from django.contrib.auth import get_user_model

User = get_user_model()

class UserService:
    """
    Service Layer containing core logic for User profiles, summaries, and avatars.
    """

    @staticmethod
    def replace_user_avatar(user, new_avatar_file) -> User:
        """
        Deletes the old avatar file from the disk storage (if exists) 
        and replaces it with the new file.
        """
        if user.profile_picture:
            old_picture_path = user.profile_picture.path
            if os.path.exists(old_picture_path):
                try:
                    os.remove(old_picture_path)
                except OSError:
                    # Ignore errors if file is blocked or already deleted
                    pass
                    
        user.profile_picture = new_avatar_file
        user.save(update_fields=['profile_picture'])
        return user

    @staticmethod
    def get_dashboard_summary(user) -> dict:
        """
        Calculates and returns user dashboard metrics, including mock structures
        for modules implemented later (Interviews, Coding, Roadmaps).
        """
        profile = UserProfile.objects.filter(user=user).first()
        stats = UserStatistics.objects.filter(user=user).first()
        
        profile_pct = profile.profile_completion_percentage if profile else 0
        streak = stats.current_streak if stats else 0
        avg_score = stats.average_score if stats else 0.0
        
        # Calculate coding progress percentage
        coding_attempts = stats.coding_attempts if stats else 0
        coding_passed = stats.coding_passed if stats else 0
        coding_progress_pct = int((coding_passed / coding_attempts * 100)) if coding_attempts > 0 else 0
        
        # Mock recent interview details
        recent_interview = {
            "title": "Mock Backend Architecture Interview",
            "role": "Senior Engineer",
            "company": "Stripe",
            "score": 84,
            "status": "Completed",
            "date": "2026-07-07"
        } if stats and stats.total_interviews > 0 else None

        # Roadmap progress representation
        roadmap_progress = {
            "completed": stats.roadmap_completed if stats else 0,
            "total_milestones": 5,
            "percentage": int((stats.roadmap_completed / 5 * 100)) if stats and stats.roadmap_completed > 0 else 0
        }

        # Select next action recommendation based on profile state
        if profile_pct < 60:
            next_action = "Complete your career profile details to get personalized recommendations."
        elif coding_attempts == 0:
            next_action = "Try your first Python Sandbox compilation challenge."
        elif stats and stats.total_interviews == 0:
            next_action = "Start your initial mock simulation session for Backend Engineering."
        else:
            next_action = "Review your performance metrics to identity weak competency nodes."

        return {
            "profile_completion_percentage": profile_pct,
            "current_streak": streak,
            "average_score": avg_score,
            "recent_interview": recent_interview,
            "coding_progress": {
                "attempts": coding_attempts,
                "passed": coding_passed,
                "success_percentage": coding_progress_pct
            },
            "roadmap_progress": roadmap_progress,
            "recommended_next_action": next_action
        }
