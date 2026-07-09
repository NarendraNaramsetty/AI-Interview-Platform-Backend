from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    TechnicalEvaluation,
    CommunicationEvaluation,
    HRBehaviorEvaluation,
    OverallEvaluation,
    EvaluationHistory
)

@receiver(post_save, sender=TechnicalEvaluation)
def log_technical_update(sender, instance, created, **kwargs):
    if not created:
        EvaluationHistory.objects.create(
            evaluation=instance.evaluation,
            action="Technical Score Updated",
            description="Technical assessment parameters adjusted by user/admin."
        )

@receiver(post_save, sender=CommunicationEvaluation)
def log_communication_update(sender, instance, created, **kwargs):
    if not created:
        EvaluationHistory.objects.create(
            evaluation=instance.evaluation,
            action="Communication Updated",
            description="Grammar, fluency, and vocal placeholders parameters modified."
        )

@receiver(post_save, sender=HRBehaviorEvaluation)
def log_hr_update(sender, instance, created, **kwargs):
    if not created:
        EvaluationHistory.objects.create(
            evaluation=instance.evaluation,
            action="HR/Behavioral Updated",
            description="Attitude, teamwork, and professionalism parameters updated."
        )

@receiver(post_save, sender=OverallEvaluation)
def log_overall_update(sender, instance, created, **kwargs):
    if not created:
        EvaluationHistory.objects.create(
            evaluation=instance.evaluation,
            action="Overall Feedback Generated",
            description="Final feedback and subsequent steps recommendations modified."
        )
