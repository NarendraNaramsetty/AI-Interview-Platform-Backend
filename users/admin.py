from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from accounts.admin import CustomUserAdmin
from .models import UserProfile, UserStatistics, Achievement, UserAchievement, UserPreference

User = get_user_model()

# Unregister the default CustomUser from accounts.admin to re-register it with users-app inlines
admin.site.unregister(User)

class UserStatisticsInline(admin.StackedInline):
    """
    Nests activity counters (interviews, streaks, scores) in UserAdmin.
    """
    model = UserStatistics
    can_delete = False
    verbose_name = _("Usage Statistic")
    verbose_name_plural = _("Usage Statistics")
    fields = [
        'total_interviews', 'completed_interviews', 'coding_attempts',
        'coding_passed', 'resumes_uploaded', 'chatbot_questions',
        'roadmap_completed', 'average_score', 'highest_score',
        'current_streak', 'total_learning_hours'
    ]
    readonly_fields = ['created_at', 'updated_at']


class UserAchievementInline(admin.TabularInline):
    """
    Nests unlocked achievements in UserAdmin.
    """
    model = UserAchievement
    extra = 1
    verbose_name = _("Earned Badge")
    verbose_name_plural = _("Earned Badges")


class UserProfileInline(admin.StackedInline):
    """
    Nests career profiles in UserAdmin.
    """
    model = UserProfile
    can_delete = False
    verbose_name = _("Career Profile")
    verbose_name_plural = _("Career Profiles")
    fields = [
        'headline', 'current_role', 'experience_level', 
        'preferred_job_role', 'preferred_company', 'preferred_interview_language',
        'target_package', 'education', 'university', 'graduation_year', 'cgpa',
        'skills', 'interests', 'github_url', 'linkedin_url', 'portfolio_url',
        'location', 'timezone', 'profile_completion_percentage'
    ]
    readonly_fields = ['profile_completion_percentage']


class CustomUserAdminWithInlines(CustomUserAdmin):
    """
    Re-registers CustomUserAdmin carrying statistics, achievements, 
    and career profile records inline.
    """
    inlines = CustomUserAdmin.inlines + (UserProfileInline, UserStatisticsInline, UserAchievementInline)


class UserPreferenceAdmin(admin.ModelAdmin):
    """
    Configuration panel for User Settings/Preferences.
    """
    list_display = ['user_email', 'dark_mode', 'preferred_theme', 'language', 'timezone']
    list_filter = ['dark_mode', 'preferred_theme', 'language']
    search_fields = ['user__email']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _("User Email")


class AchievementAdmin(admin.ModelAdmin):
    """
    Configuration panel for global Achievement Badges.
    """
    list_display = ['title', 'points', 'category', 'badge_icon']
    list_filter = ['category', 'points']
    search_fields = ['title', 'description']


admin.site.register(User, CustomUserAdminWithInlines)
admin.site.register(UserPreference, UserPreferenceAdmin)
admin.site.register(Achievement, AchievementAdmin)
