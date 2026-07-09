from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InterviewQuestion, QuestionHistory

@receiver(post_save, sender=InterviewQuestion)
def auto_log_question_history(sender, instance, created, **kwargs):
    """
    Auto-records auditable actions (Created / Updated) in QuestionHistory.
    """
    if created:
        QuestionHistory.objects.create(
            question=instance,
            action='Created',
            description="Interview question created and registered in bank.",
            performed_by=instance.created_by
        )
    else:
        # Check if this update was triggered by an import tool or duplicate action.
        # We can pass custom attributes on the instance to refine this log if needed,
        # but defaulting to 'Updated' handles normal edits cleanly.
        action = getattr(instance, '_history_action', 'Updated')
        desc = getattr(instance, '_history_description', "Question metadata modified.")
        
        QuestionHistory.objects.create(
            question=instance,
            action=action,
            description=desc,
            performed_by=instance.created_by
        )
