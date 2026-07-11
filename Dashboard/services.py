from django.db.models import Avg, Max
from django.utils import timezone

# Safe imports from companion apps
from users.models import UserProfile
from resume.models import Resume
from interviews.models import InterviewSession
from coding.models import CodeSubmission, CodingScore
from roadmap.models import UserRoadmap
from chatbot.models import ChatSession

class DashboardService:
    """
    Service layer executing direct database metrics aggregation.
    """

    @classmethod
    def get_candidate_statistics(cls, user) -> dict:
        """
        Gathers dashboard widget counters.
        """
        # 1. Profile statistics
        profile = UserProfile.objects.filter(user=user).select_related('user', 'user__statistics').first()
        points = 0
        if profile and hasattr(profile.user, 'statistics'):
            points = profile.user.statistics.highest_score

        profile_data = {
            "ranking_points": points,
            "experience_level": profile.experience_level if profile else "Junior",
            "target_role": profile.preferred_job_role if profile else ""
        }

        # 2. Resumes metrics
        resumes = Resume.objects.filter(user=user)
        resumes_count = resumes.count()
        last_resume = resumes.order_by('-created_at').first()
        
        ats_score = 0
        if last_resume:
            try:
                if hasattr(last_resume, 'analysis') and last_resume.analysis:
                    ats_score = last_resume.analysis.ats_score
            except Exception:
                pass

        resumes_data = {
            "total_resumes": resumes_count,
            "last_resume_score": ats_score,
            "last_resume_id": last_resume.id if last_resume else None
        }

        # 3. Interviews metrics
        interviews = InterviewSession.objects.filter(user=user).select_related('result')
        interviews_count = interviews.count()
        # Calculate average rating of completed interviews
        avg_rating = interviews.aggregate(Avg('result__overall_score'))['result__overall_score__avg'] or 0.0
        recent_interviews = interviews.order_by('-created_at')[:3]
        recent_list = []
        for i in recent_interviews:
            score_val = i.result.overall_score if hasattr(i, 'result') else 0
            recent_list.append({
                "id": i.id,
                "title": f"Interview {i.id}",
                "status": i.status,
                "score": score_val,
                "created_at": i.created_at
            })
        interviews_data = {
            "total_interviews": interviews_count,
            "average_score": round(float(avg_rating), 2),
            "recent_interviews": recent_list
        }

        # 4. Coding metrics
        try:
            from coding.services import CodingService
            coding_stats = CodingService.get_user_statistics(user)
            coding_data = {
                "solved_challenges": coding_stats.get("problems_solved", 0),
                "streak": coding_stats.get("current_streak", 0),
                "preferred_language": coding_stats.get("preferred_language", "Python")
            }
        except Exception:
            coding_data = {
                "solved_challenges": 0,
                "streak": 0,
                "preferred_language": "Python"
            }

        # 5. Roadmap metrics
        roadmaps = UserRoadmap.objects.filter(user=user)
        completed_count = roadmaps.filter(status='Completed').count()
        active_roadmap = roadmaps.filter(status='In Progress').first()
        roadmap_data = {
            "completed_roadmaps": completed_count,
            "active_roadmap_title": active_roadmap.roadmap.title if active_roadmap else None,
            "active_roadmap_progress": active_roadmap.progress_percentage if active_roadmap else 0.0
        }

        return {
            "profile": profile_data,
            "resumes": resumes_data,
            "interviews": interviews_data,
            "coding": coding_data,
            "roadmap": roadmap_data
        }

    @classmethod
    def get_recent_activity(cls, user, limit: int = 10) -> list:
        """
        Assembles recent timeline activity feeds list.
        """
        activities = []

        # Query interviews
        for item in InterviewSession.objects.filter(user=user).order_by('-created_at')[:limit]:
            activities.append({
                "type": "interview",
                "title": f"Started Interview Session",
                "description": f"Session status: {item.status}",
                "timestamp": item.created_at
            })

        # Query code submissions
        for item in CodeSubmission.objects.filter(user=user).order_by('-created_at')[:limit]:
            activities.append({
                "type": "coding",
                "title": f"Submitted code solution",
                "description": f"Outcome: {item.status} ({item.language})",
                "timestamp": item.created_at
            })

        # Query chatbot sessions
        for item in ChatSession.objects.filter(user=user).order_by('-created_at')[:limit]:
            activities.append({
                "type": "chatbot",
                "title": f"Started AI chatbot session",
                "description": f"Session: {item.title}",
                "timestamp": item.created_at
            })

        # Query roadmaps
        for item in UserRoadmap.objects.filter(user=user).order_by('-started_at')[:limit]:
            activities.append({
                "type": "roadmap",
                "title": f"Enrolled in career roadmap",
                "description": f"Progress: {item.progress_percentage}% ({item.status})",
                "timestamp": item.started_at
            })

        # Sort combined activities by timestamp desc
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]
