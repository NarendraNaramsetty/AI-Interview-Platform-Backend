import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify

from .constants import (
    DIFFICULTY_CHOICES,
    DIFFICULTY_MEDIUM,
    SUBMISSION_STATUS_CHOICES,
    STATUS_PENDING,
    PROGRAMMING_LANGUAGE_CHOICES,
    LANG_PYTHON
)
from .validators import (
    validate_programming_language,
    validate_source_code_length
)

class CodingCategory(models.Model):
    """
    Groups coding challenges by topic (e.g. Arrays, Recursion, Trees, SQL).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Coding Category"
        verbose_name_plural = "Coding Categories"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class CodingProblem(models.Model):
    """
    Core coding problem definition containing problem specifications, input/output schemas,
    execution bounds, points, hints, and category links.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    problem_statement = models.TextField()
    input_format = models.TextField(blank=True)
    output_format = models.TextField(blank=True)
    constraints = models.TextField(blank=True)
    
    # Examples
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    
    difficulty = models.CharField(
        max_length=50,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_MEDIUM
    )
    category = models.ForeignKey(
        CodingCategory,
        on_delete=models.CASCADE,
        related_name='problems'
    )
    company = models.ForeignKey(
        'questions.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coding_problems'
    )
    
    tags = models.JSONField(default=list, blank=True)
    hints = models.JSONField(default=list, blank=True)
    
    time_limit = models.FloatField(default=1.0)  # in seconds
    memory_limit = models.IntegerField(default=256)  # in MB
    acceptance_rate = models.FloatField(default=0.0)  # percentage
    points = models.IntegerField(default=10)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class TestCase(models.Model):
    """
    Test cases to run inputs against compilers and assert output validity.
    """
    problem = models.ForeignKey(
        CodingProblem,
        on_delete=models.CASCADE,
        related_name='test_cases'
    )
    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=True)

    def __str__(self):
        type_str = "Sample" if self.is_sample else "Hidden"
        return f"Test Case for {self.problem.title} - Type: {type_str}"


class CodeSubmission(models.Model):
    """
    Represents draft saves or final submissions for code files.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coding_submissions'
    )
    problem = models.ForeignKey(
        CodingProblem,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    programming_language = models.CharField(
        max_length=50,
        choices=PROGRAMMING_LANGUAGE_CHOICES,
        default=LANG_PYTHON,
        validators=[validate_programming_language]
    )
    source_code = models.TextField(validators=[validate_source_code_length])
    
    execution_time = models.FloatField(default=0.0)  # in seconds
    memory_used = models.FloatField(default=0.0)  # in MB
    passed_test_cases = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    
    status = models.CharField(
        max_length=50,
        choices=SUBMISSION_STATUS_CHOICES,
        default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {self.uuid} - {self.user.email} - Status: {self.status}"


class CodingScore(models.Model):
    """
    Points database record generated automatically upon successful runs.
    """
    submission = models.OneToOneField(
        CodeSubmission,
        on_delete=models.CASCADE,
        related_name='score_record'
    )
    score = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    ranking_points = models.IntegerField(default=0)
    feedback_placeholder = models.TextField(blank=True)

    def __str__(self):
        return f"Score card for Sub: {self.submission.id} - Points: {self.ranking_points}"


class CodingHistory(models.Model):
    """
    Audit registry to log coding activity (Problem Started, Code Saved, Code Submitted, Evaluation Completed).
    """
    submission = models.ForeignKey(
        CodeSubmission,
        on_delete=models.CASCADE,
        related_name='history_logs'
    )
    action = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Coding History"
        verbose_name_plural = "Coding Histories"

    def __str__(self):
        return f"{self.action} - Sub: {self.submission.id} at {self.timestamp}"


class FavoriteProblem(models.Model):
    """
    Bookmarks list supporting standard candidate favorites items.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_problems'
    )
    problem = models.ForeignKey(
        CodingProblem,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'problem')

    def __str__(self):
        return f"Favorite: {self.user.email} -> {self.problem.title}"
