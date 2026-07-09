import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from interviews.models import InterviewSession

from .constants import (
    EVALUATION_STATUS_CHOICES,
    STATUS_PENDING,
    OVERALL_RATING_CHOICES,
    RATING_AVERAGE,
    PRIORITY_CHOICES,
    PRIORITY_MEDIUM,
    RESOURCE_TYPE_CHOICES,
    RESOURCE_COURSE
)
from .validators import (
    validate_score_range,
    validate_feedback_length,
    validate_suggestion_priority,
    validate_resource_url
)

class InterviewEvaluation(models.Model):
    """
    Main evaluation record linked to an Interview Session and User.
    Tracks parsing status and execution timestamps.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    interview = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    evaluation_status = models.CharField(
        max_length=50,
        choices=EVALUATION_STATUS_CHOICES,
        default=STATUS_PENDING
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Evaluation {self.uuid} - Session: {self.interview.id} - Status: {self.evaluation_status}"


class TechnicalEvaluation(models.Model):
    """
    Evaluation metrics for programming languages, algorithms, designs, and explanation quality.
    """
    evaluation = models.OneToOneField(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='technical_evaluation'
    )
    technical_score = models.IntegerField(default=0, validators=[validate_score_range])
    coding_score = models.IntegerField(default=0, validators=[validate_score_range])
    problem_solving_score = models.IntegerField(default=0, validators=[validate_score_range])
    database_score = models.IntegerField(default=0, validators=[validate_score_range])
    algorithm_score = models.IntegerField(default=0, validators=[validate_score_range])
    explanation_quality = models.IntegerField(default=0, validators=[validate_score_range])
    
    # Store list of strings representing bullet points
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Technical Evaluation for Eval: {self.evaluation.id} - Score: {self.technical_score}"


class CommunicationEvaluation(models.Model):
    """
    Evaluation scores on voice grammar, vocabulary, clarity, fluency, and placeholders.
    """
    evaluation = models.OneToOneField(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='communication_evaluation'
    )
    communication_score = models.IntegerField(default=0, validators=[validate_score_range])
    grammar_score = models.IntegerField(default=0, validators=[validate_score_range])
    fluency_score = models.IntegerField(default=0, validators=[validate_score_range])
    vocabulary_score = models.IntegerField(default=0, validators=[validate_score_range])
    clarity_score = models.IntegerField(default=0, validators=[validate_score_range])
    
    # Placeholders for future Whisper transcript analysis
    pronunciation_score_placeholder = models.IntegerField(default=0, validators=[validate_score_range])
    confidence_score_placeholder = models.IntegerField(default=0, validators=[validate_score_range])

    def __str__(self):
        return f"Communication Evaluation for Eval: {self.evaluation.id} - Score: {self.communication_score}"


class HRBehaviorEvaluation(models.Model):
    """
    Core assessments of applicant attitude, professionalism, and team dynamics.
    """
    evaluation = models.OneToOneField(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='hr_evaluation'
    )
    confidence_score = models.IntegerField(default=0, validators=[validate_score_range])
    professionalism_score = models.IntegerField(default=0, validators=[validate_score_range])
    leadership_score = models.IntegerField(default=0, validators=[validate_score_range])
    teamwork_score = models.IntegerField(default=0, validators=[validate_score_range])
    adaptability_score = models.IntegerField(default=0, validators=[validate_score_range])
    attitude_score = models.IntegerField(default=0, validators=[validate_score_range])
    behavioral_feedback = models.TextField(blank=True)

    def __str__(self):
        return f"HR Evaluation for Eval: {self.evaluation.id}"


class OverallEvaluation(models.Model):
    """
    Final feedback summaries, rating levels, and customized subsequent roadmap guidelines.
    """
    evaluation = models.OneToOneField(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='overall_evaluation'
    )
    overall_score = models.IntegerField(default=0, validators=[validate_score_range])
    overall_rating = models.CharField(
        max_length=50,
        choices=OVERALL_RATING_CHOICES,
        default=RATING_AVERAGE
    )
    recommendation = models.CharField(max_length=255, blank=True)
    final_feedback = models.TextField(blank=True)
    next_learning_plan = models.TextField(blank=True)

    def __str__(self):
        return f"Overall Evaluation for Eval: {self.evaluation.id} - Score: {self.overall_score}"


class ImprovementSuggestion(models.Model):
    """
    Targeted instructions suggesting improvement actions mapped by categories and severity.
    """
    evaluation = models.ForeignKey(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='suggestions'
    )
    category = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(validators=[validate_feedback_length])
    priority = models.CharField(
        max_length=50,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        validators=[validate_suggestion_priority]
    )

    def __str__(self):
        return f"Suggestion: {self.title} ({self.priority})"


class RecommendedResource(models.Model):
    """
    External study links recommended by AI matching weak spots.
    """
    evaluation = models.ForeignKey(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=50,
        choices=RESOURCE_TYPE_CHOICES,
        default=RESOURCE_COURSE
    )
    url = models.URLField(validators=[validate_resource_url])
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Resource: {self.title} - Type: {self.type}"


class EvaluationHistory(models.Model):
    """
    Audit log capturing changes to technical metrics, comments updates, or generation timing.
    """
    evaluation = models.ForeignKey(
        InterviewEvaluation,
        on_delete=models.CASCADE,
        related_name='history_logs'
    )
    action = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f"History Log: {self.action} on Eval {self.evaluation.id} at {self.performed_at}"
