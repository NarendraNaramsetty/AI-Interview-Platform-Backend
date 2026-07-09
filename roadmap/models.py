import uuid
from django.db import models
from django.conf import settings
from .constants import (
    DIFFICULTY_CHOICES,
    DIFFICULTY_MEDIUM,
    MODULE_TYPE_CHOICES,
    TYPE_VIDEO,
    RESOURCE_TYPE_CHOICES,
    RES_WEBSITE,
    ROADMAP_STATUS_CHOICES,
    STATUS_NOT_STARTED,
    REMINDER_FREQUENCY_CHOICES,
    FREQ_DAILY
)
from .validators import validate_percentage_range, validate_reminder_time

class CareerPath(models.Model):
    """
    Broad career trajectory paths (e.g. AI Engineer, Python Developer).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Lucide or Heroicon name tag")
    estimated_duration = models.CharField(max_length=100, help_text="e.g. 6 Months")
    difficulty = models.CharField(
        max_length=50,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_MEDIUM
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Career Path"
        verbose_name_plural = "Career Paths"

    def __str__(self):
        return self.name


class Roadmap(models.Model):
    """
    Sequential learning path templates matching a specific CareerPath.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    career_path = models.ForeignKey(
        CareerPath,
        on_delete=models.CASCADE,
        related_name='roadmaps'
    )
    estimated_duration = models.CharField(max_length=100)
    total_modules = models.IntegerField(default=0)
    difficulty = models.CharField(
        max_length=50,
        choices=DIFFICULTY_CHOICES,
        default=DIFFICULTY_MEDIUM
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class RoadmapModule(models.Model):
    """
    Modular milestones inside a Learning Roadmap.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    module_order = models.IntegerField(default=1)
    estimated_hours = models.IntegerField(default=1)
    module_type = models.CharField(
        max_length=50,
        choices=MODULE_TYPE_CHOICES,
        default=TYPE_VIDEO
    )

    class Meta:
        ordering = ['module_order', 'id']
        verbose_name = "Roadmap Module"
        verbose_name_plural = "Roadmap Modules"

    def __str__(self):
        return f"{self.roadmap.title} - M{self.module_order}: {self.title}"


class LearningResource(models.Model):
    """
    Specific learning resources linked to a roadmap module (YouTube, Articles, Courses).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    roadmap_module = models.ForeignKey(
        RoadmapModule,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    title = models.CharField(max_length=255)
    resource_type = models.CharField(
        max_length=50,
        choices=RESOURCE_TYPE_CHOICES,
        default=RES_WEBSITE
    )
    provider = models.CharField(max_length=150, blank=True)
    url = models.URLField()
    duration = models.IntegerField(default=0, help_text="Duration in minutes")
    is_free = models.BooleanField(default=True)

    class Meta:
        ordering = ['title']
        verbose_name = "Learning Resource"
        verbose_name_plural = "Learning Resources"

    def __str__(self):
        return f"{self.title} ({self.resource_type})"


class UserRoadmap(models.Model):
    """
    Individual progress tracker mapping a candidate user to an active roadmap.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_roadmaps'
    )
    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name='user_progresses'
    )
    progress_percentage = models.FloatField(
        default=0.0,
        validators=[validate_percentage_range]
    )
    completed_modules = models.IntegerField(default=0)
    current_module = models.ForeignKey(
        RoadmapModule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_in_roadmaps'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=ROADMAP_STATUS_CHOICES,
        default=STATUS_NOT_STARTED
    )

    class Meta:
        ordering = ['-started_at']
        verbose_name = "User Roadmap"
        verbose_name_plural = "User Roadmaps"

    def __str__(self):
        return f"UserRoadmap: {self.user.email} -> {self.roadmap.title} ({self.progress_percentage}%)"


class ModuleProgress(models.Model):
    """
    Details which modules a user completed, when, and matching notes.
    """
    user_roadmap = models.ForeignKey(
        UserRoadmap,
        on_delete=models.CASCADE,
        related_name='module_progresses'
    )
    roadmap_module = models.ForeignKey(
        RoadmapModule,
        on_delete=models.CASCADE,
        related_name='progresses'
    )
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('user_roadmap', 'roadmap_module')
        verbose_name = "Module Progress"
        verbose_name_plural = "Module Progresses"

    def __str__(self):
        status_str = "Done" if self.is_completed else "Todo"
        return f"Progress: {self.user_roadmap.user.email} - Module {self.roadmap_module.id} -> {status_str}"


class LearningReminder(models.Model):
    """
    Reminder notification controls mapping reminder times and weekly frequencies.
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_time = models.TimeField(validators=[validate_reminder_time])
    frequency = models.CharField(
        max_length=50,
        choices=REMINDER_FREQUENCY_CHOICES,
        default=FREQ_DAILY
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['reminder_time']
        verbose_name = "Learning Reminder"
        verbose_name_plural = "Learning Reminders"

    def __str__(self):
        return f"Reminder: {self.user.email} for {self.roadmap.title} at {self.reminder_time}"
