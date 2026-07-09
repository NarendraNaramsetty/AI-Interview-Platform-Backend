from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CodeSubmission, CodingProblem
from .constants import STATUS_ACCEPTED, STATUS_PENDING

@receiver(post_save, sender=CodeSubmission)
def update_problem_acceptance_rate(sender, instance, created, **kwargs):
    """
    Fires upon solution evaluations to recalculate and update a problem's
    acceptance rate dynamically. Excludes 'Pending' autosave drafts.
    """
    if instance.status != STATUS_PENDING:
        problem = instance.problem
        # Exclude draft autosaves when counting submission items
        total = CodeSubmission.objects.filter(problem=problem).exclude(status=STATUS_PENDING).count()
        accepted = CodeSubmission.objects.filter(problem=problem, status=STATUS_ACCEPTED).count()

        if total > 0:
            problem.acceptance_rate = round((accepted / total) * 100, 2)
        else:
            problem.acceptance_rate = 0.0
            
        problem.save(update_fields=['acceptance_rate'])
