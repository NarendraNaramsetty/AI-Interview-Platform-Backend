from django.db import models
from django.conf import settings
from .validators import (
    validate_cgpa,
    validate_graduation_year,
    validate_json_string_list,
    validate_github_profile_url,
    validate_linkedin_profile_url
)

class UserProfile(models.Model):
    """
    Detailed developer career and education profile linked OneToOne with CustomUser.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    headline = models.CharField(max_length=255, blank=True)
    current_role = models.CharField(max_length=100, blank=True)
    experience_level = models.CharField(max_length=50, blank=True)
    preferred_job_role = models.CharField(max_length=100, blank=True)
    preferred_company = models.CharField(max_length=100, blank=True)
    preferred_interview_language = models.CharField(max_length=50, blank=True)
    target_package = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Education
    education = models.CharField(max_length=255, blank=True)
    university = models.CharField(max_length=255, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True, validators=[validate_graduation_year])
    cgpa = models.FloatField(null=True, blank=True, validators=[validate_cgpa])
    
    # Structured tags arrays
    skills = models.JSONField(default=list, blank=True, validators=[validate_json_string_list])
    interests = models.JSONField(default=list, blank=True, validators=[validate_json_string_list])
    
    # Portfolio Links
    github_url = models.URLField(blank=True, validators=[validate_github_profile_url])
    linkedin_url = models.URLField(blank=True, validators=[validate_linkedin_profile_url])
    portfolio_url = models.URLField(blank=True)
    
    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=100, blank=True)
    profile_completion_percentage = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_completion(self) -> int:
        """
        Dynamically calculates the profile completion percentage based on filled parameters.
        """
        fields_to_check = [
            'headline', 'current_role', 'experience_level', 
            'preferred_job_role', 'preferred_company', 'preferred_interview_language',
            'education', 'university', 'graduation_year', 'cgpa',
            'github_url', 'linkedin_url', 'portfolio_url', 'location'
        ]
        
        filled = sum(1 for field in fields_to_check if getattr(self, field))
        
        # Check JSON arrays
        if self.skills:
            filled += 1
        if self.interests:
            filled += 1
            
        total_fields = len(fields_to_check) + 2
        return int((filled / total_fields) * 100)

    def save(self, *args, **kwargs):
        self.profile_completion_percentage = self.calculate_completion()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} Profile"


class UserStatistics(models.Model):
    """
    Platform usage indicators and performance aggregates.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='statistics'
    )
    total_interviews = models.IntegerField(default=0)
    completed_interviews = models.IntegerField(default=0)
    coding_attempts = models.IntegerField(default=0)
    coding_passed = models.IntegerField(default=0)
    resumes_uploaded = models.IntegerField(default=0)
    chatbot_questions = models.IntegerField(default=0)
    roadmap_completed = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    highest_score = models.FloatField(default=0.0)
    current_streak = models.IntegerField(default=0)
    total_learning_hours = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} Statistics"


class Achievement(models.Model):
    """
    System-wide achievements badge directory.
    """
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    badge_icon = models.CharField(max_length=100, blank=True)  # Lucide icon tag (e.g. 'award', 'zap')
    points = models.IntegerField(default=0)
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    """
    Many-to-Many earning record between a CustomUser and unlocked Achievements.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='earned_achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='earners'
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.email} - {self.achievement.title}"


class UserPreference(models.Model):
    """
    Global UI theme preferences and notification alerts switches.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    dark_mode = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    preferred_theme = models.CharField(max_length=50, default='default')
    interview_difficulty = models.CharField(max_length=50, default='Intermediate')
    
    preferred_roles = models.JSONField(default=list, blank=True, validators=[validate_json_string_list])
    preferred_companies = models.JSONField(default=list, blank=True, validators=[validate_json_string_list])
    
    language = models.CharField(max_length=50, default='English')
    timezone = models.CharField(max_length=100, default='UTC')

    def __str__(self):
        return f"{self.user.email} Preferences"
