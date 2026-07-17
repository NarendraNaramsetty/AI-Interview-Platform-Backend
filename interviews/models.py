import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from resume.models import Resume
from .constants import (
    DIFFICULTY_CHOICES,
    INTERVIEW_TYPE_CHOICES,
    MODE_CHOICES,
    STATUS_CHOICES,
    SOURCE_CHOICES,
    ANSWER_TYPE_CHOICES,
    STATUS_SCHEDULED
)
from .validators import validate_question_count, validate_duration_range, validate_audio_file_size

class InterviewSessionQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class InterviewSessionManager(models.Manager):
    def get_queryset(self):
        return InterviewSessionQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return super().get_queryset()


class InterviewSession(models.Model):
    """
    Core model representing an interview prep session configured by a user.
    Supports soft deletes, type choices, tracking pointers, and timestamps.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_sessions'
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )
    title = models.CharField(max_length=255)
    target_role = models.CharField(max_length=255)
    target_company = models.CharField(max_length=255)
    
    interview_type = models.CharField(max_length=50, choices=INTERVIEW_TYPE_CHOICES)
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)
    interview_mode = models.CharField(max_length=50, choices=MODE_CHOICES)
    language = models.CharField(max_length=100, default='English')
    
    total_questions = models.IntegerField(validators=[validate_question_count])
    answered_questions = models.IntegerField(default=0)
    current_question_index = models.IntegerField(default=0)  # Pointer index of sequence flow
    
    duration_minutes = models.IntegerField(validators=[validate_duration_range])
    elapsed_time_seconds = models.IntegerField(default=0)
    tech_stack = models.JSONField(default=list, blank=True)
    adaptive_mode = models.BooleanField(default=True)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = InterviewSessionManager()

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.status}) - {self.user.email}"


class InterviewQuestion(models.Model):
    """
    Model holding the individual questions associated with a session.
    Note: Questions are loaded from mock files/DB and populated later by AI modules.
    """
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.TextField()
    topic = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=100, blank=True)
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)
    sequence_number = models.IntegerField()  # Order sequence inside session
    
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='Database')
    expected_answer_placeholder = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence_number']

    def __str__(self):
        return f"Q{self.sequence_number}: {self.question_text[:50]}..."


class InterviewAnswer(models.Model):
    """
    Stores answer transcripts, durations, types, and voice file attachments (metadata only).
    """
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        InterviewQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    answer_text = models.TextField()
    answer_type = models.CharField(max_length=50, choices=ANSWER_TYPE_CHOICES, default='Text')
    audio_file = models.FileField(
        upload_to='answers_audio/', 
        null=True, 
        blank=True,
        validators=[validate_audio_file_size]
    )
    answer_duration = models.IntegerField(default=0)  # Duration in seconds
    score = models.IntegerField(null=True, blank=True)
    feedback = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to Q{self.question.sequence_number} - {self.session.user.email}"


class InterviewProgress(models.Model):
    """
    State parameters tracking completed percentages and timers.
    """
    session = models.OneToOneField(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    percentage_completed = models.FloatField(default=0.0)
    current_question = models.ForeignKey(
        InterviewQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    remaining_questions = models.IntegerField(default=0)
    elapsed_time = models.IntegerField(default=0)  # In seconds
    estimated_remaining_time = models.IntegerField(default=0)  # In seconds
    last_saved_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress: {self.session.title} ({self.percentage_completed}%)"


class InterviewResult(models.Model):
    """
    Placeholder evaluation scorecards created upon session completions.
    """
    session = models.OneToOneField(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='result'
    )
    technical_score = models.IntegerField(default=0)
    communication_score = models.IntegerField(default=0)
    confidence_score = models.IntegerField(default=0)
    grammar_score = models.IntegerField(default=0)
    overall_score = models.IntegerField(default=0)
    
    status = models.CharField(max_length=50, default='Pending')
    feedback_placeholder = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result: {self.session.title} - Overall Score: {self.overall_score}"


class InterviewTimeline(models.Model):
    """
    Auditable lifecycle activities registry (started, paused, skipped, completed).
    """
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='timeline_events'
    )
    action = models.CharField(max_length=150)  # e.g., 'Interview Started', 'Question Answered'
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.title} - {self.action} at {self.timestamp}"
