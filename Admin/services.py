import csv
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse

# Imports from companion apps
from Payments.models import UserSubscription
from interviews.models import InterviewSession
from coding.models import CodeSubmission
from users.models import UserProfile

User = get_user_model()

class AdminService:
    """
    Service layer providing system metrics aggregates and CSV data reports.
    """

    @classmethod
    def get_platform_analytics(cls) -> dict:
        """
        Calculates total user counts, active subscriptions, total evaluations, and MRR.
        """
        total_users = User.objects.count()
        
        active_subs = UserSubscription.objects.filter(status='Active')
        active_subs_count = active_subs.count()
        
        # Calculate MRR (Monthly Recurring Revenue)
        mrr = active_subs.aggregate(Sum('plan__price'))['plan__price__sum'] or 0.0

        total_interviews = InterviewSession.objects.count()
        total_submissions = CodeSubmission.objects.count()

        return {
            "total_users": total_users,
            "active_subscriptions": active_subs_count,
            "monthly_recurring_revenue": float(mrr),
            "total_interviews_conducted": total_interviews,
            "total_submissions_evaluated": total_submissions
        }

    @classmethod
    def export_users_csv(cls) -> HttpResponse:
        """
        Compiles all candidate profiles into a CSV file stream.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="candidate_users.csv"'

        writer = csv.writer(response)
        writer.writerow(['User ID', 'Email', 'First Name', 'Last Name', 'Experience Level', 'Target Role', 'Ranking Points'])

        profiles = UserProfile.objects.select_related('user', 'user__statistics').all()
        for p in profiles:
            points = p.user.statistics.highest_score if hasattr(p.user, 'statistics') else 0
            writer.writerow([
                p.user.id,
                p.user.email,
                p.user.first_name,
                p.user.last_name,
                p.experience_level,
                p.preferred_job_role,
                points
            ])

        return response

    @classmethod
    def export_interviews_csv(cls) -> HttpResponse:
        """
        Compiles all interview session logs into a CSV file stream.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="interview_sessions.csv"'

        writer = csv.writer(response)
        writer.writerow(['Session ID', 'User Email', 'Resume ID', 'Target Role', 'Overall Score', 'Status', 'Created At'])

        sessions = InterviewSession.objects.select_related('user', 'resume', 'result').all()
        for s in sessions:
            score = s.result.overall_score if hasattr(s, 'result') else 0
            writer.writerow([
                s.id,
                s.user.email,
                s.resume.id if s.resume else 'N/A',
                s.target_role,
                score,
                s.status,
                s.created_at
            ])

        return response
