import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .constants import DIFFICULTY_CHOICES, SOURCE_CHOICES, ANSWER_TYPE_CHOICES_LIST
from .validators import validate_question_text_length, validate_expected_duration, validate_attachment_file_size

class QuestionCategory(models.Model):
    """
    Groups questions by primary skill groups/languages (e.g. Python, SQL, HR, React).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Lucide or Heroicon identifier name")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Question Category")
        verbose_name_plural = _("Question Categories")
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Company(models.Model):
    """
    Corporate references to associate target interview questions (e.g. Google, Microsoft).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=150, unique=True)
    logo = models.ImageField(upload_to='companies_logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ['name']

    def __str__(self):
        return self.name


class JobRole(models.Model):
    """
    Specific job postings targeting preparation (e.g. Frontend Developer, ML Engineer).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    experience_level = models.CharField(max_length=100, default='Any')  # Junior, Mid, Senior, Lead
    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_roles'
    )

    class Meta:
        verbose_name = _("Job Role")
        verbose_name_plural = _("Job Roles")
        unique_together = ['title', 'experience_level']
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.experience_level})"


class Topic(models.Model):
    """
    Granular concept topics nested under parent Categories (e.g. OOP, REST API, CNN).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")
        unique_together = ['category', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class QuestionTag(models.Model):
    """
    Simple tag metadata labeling technical questions.
    """
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default='#6366F1')  # Hex colors

    class Meta:
        verbose_name = _("Question Tag")
        verbose_name_plural = _("Question Tags")
        ordering = ['name']

    def __str__(self):
        return self.name


class InterviewQuestion(models.Model):
    """
    Database of preparation questions containing prompts, hints, expected answers, and filters.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    question = models.TextField(validators=[validate_question_text_length])
    short_description = models.CharField(max_length=255, blank=True)
    
    category = models.ForeignKey(
        QuestionCategory,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions'
    )
    role = models.ForeignKey(
        JobRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions'
    )
    
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)
    expected_duration = models.IntegerField(validators=[validate_expected_duration], help_text="Duration in minutes")
    answer_type = models.CharField(max_length=50, choices=ANSWER_TYPE_CHOICES_LIST, default='Text')
    
    # Metadata fields stored as JSON arrays
    tags = models.JSONField(default=list, blank=True, help_text="Array of string tag tags")
    hints = models.JSONField(default=list, blank=True, help_text="Helper pointers tips list")
    reference_links = models.JSONField(default=list, blank=True, help_text="Markdown URLs list")
    
    expected_answer = models.TextField(blank=True, help_text="Answer keyword templates check")
    explanation = models.TextField(blank=True, help_text="Conceptual walkthrough detailing solution steps")
    
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='Manual')
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_questions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Interview Question")
        verbose_name_plural = _("Interview Questions")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.question[:60]}... ({self.category.name})"


class QuestionAttachment(models.Model):
    """
    Supporting attachment items like coding files, images, or PDFs schemas files.
    """
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(
        InterviewQuestion,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='questions_attachments/',
        validators=[validate_attachment_file_size]
    )
    file_type = models.CharField(max_length=100)  # e.g., 'image/png', 'application/pdf'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.id} for Question {self.question.id}"


class QuestionHistory(models.Model):
    """
    Logs auditable updates, duplicates, and spreadsheet import history entries.
    """
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(
        InterviewQuestion,
        on_delete=models.CASCADE,
        related_name='history_logs'
    )
    action = models.CharField(max_length=100)  # Created, Updated, Deleted, Imported, Exported
    description = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Question History Log")
        verbose_name_plural = _("Question History Logs")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.question.id} - {self.action} at {self.timestamp}"
