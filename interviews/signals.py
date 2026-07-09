from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import InterviewSession, InterviewProgress, InterviewResult, InterviewTimeline
from .constants import STATUS_COMPLETED

@receiver(post_save, sender=InterviewSession)
def create_session_related_records(sender, instance, created, **kwargs):
    """
    Auto-creates InterviewProgress records and logs timelines on creations.
    Automatically instantiates a blank InterviewResult when status transitions to Completed.
    """
    if created:
        # Create blank progress tracking record
        InterviewProgress.objects.get_or_create(
            session=instance,
            remaining_questions=instance.total_questions
        )
        
        # Log session registration event
        InterviewTimeline.objects.create(
            session=instance,
            action='Interview Created',
            description=f"Interview session for role '{instance.target_role}' configured and scheduled."
        )
    else:
        # Check status transitions triggers
        # If marked completed, prepare mock scores scorecard
        if instance.status == STATUS_COMPLETED:
            InterviewResult.objects.get_or_create(
                session=instance,
                technical_score=0,
                communication_score=0,
                confidence_score=0,
                grammar_score=0,
                overall_score=0,
                status='Pending',
                feedback_placeholder="Awaiting AI analysis evaluation feedback reports..."
            )
            
            # Record completed time
            if not instance.completed_at:
                # Bypass post_save loop by using update
                InterviewSession.objects.filter(id=instance.id).update(completed_at=timezone.now())
