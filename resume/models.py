import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class ResumeQuerySet(models.QuerySet):
    """
    QuerySet for custom filtering on active and soft-deleted records.
    """
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class ResumeManager(models.Manager):
    """
    Model manager that filters out soft-deleted records by default.
    """
    def get_queryset(self):
        return ResumeQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return super().get_queryset()


class Resume(models.Model):
    """
    Model storing parsed resume documents, version counts, default states, and text content.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes'
    )
    title = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='resumes/')
    file_size = models.IntegerField()  # Size in bytes
    file_type = models.CharField(max_length=50)  # e.g., 'pdf', 'docx'
    resume_version = models.IntegerField(default=1)
    
    resume_text = models.TextField(blank=True)
    total_pages = models.IntegerField(default=1)
    upload_source = models.CharField(max_length=50, default='Web')
    
    # Status properties
    status = models.CharField(max_length=50, default='Active')  # e.g. Active, Archived
    processing_status = models.CharField(max_length=50, default='Pending')  # e.g. Pending, Completed, Failed
    is_default = models.BooleanField(default=False)
    
    # Hash for duplicate checking
    file_hash = models.CharField(max_length=64, blank=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = ResumeManager()

    def delete(self, *args, **kwargs):
        """
        Soft deletes the record by stamping deleted_at.
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        """
        Restores a soft-deleted record.
        """
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, *args, **kwargs):
        """
        Actually deletes the record from the database table.
        """
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (v{self.resume_version}) - {self.user.email}"


class ResumeAnalysis(models.Model):
    """
    AI assessment data structures associated with parsed resumes.
    """
    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    overall_score = models.IntegerField(default=0)
    ats_score = models.IntegerField(default=0)
    grammar_score = models.IntegerField(default=0)
    keyword_score = models.IntegerField(default=0)
    completeness_score = models.IntegerField(default=0)
    
    summary = models.TextField(blank=True)
    
    # Assessments structured elements
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    recommended_roles = models.JSONField(default=list, blank=True)
    
    analysis_status = models.CharField(max_length=50, default='Pending')  # e.g. Pending, Completed, Failed
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis: {self.resume.title} - Score: {self.overall_score}"


class ResumeActivity(models.Model):
    """
    Auditing user transactions with resumes (uploads, replacements, downloads).
    """
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    action = models.CharField(max_length=100)  # e.g. 'Uploaded Resume', 'Deleted Resume'
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resume.title} - {self.action} at {self.created_at}"
