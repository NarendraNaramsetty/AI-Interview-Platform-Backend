from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import Resume, ResumeAnalysis, ResumeActivity

class ResumeAnalysisInline(admin.StackedInline):
    """
    Inlines AI Assessment summaries directly inside the Resume details panel.
    """
    model = ResumeAnalysis
    can_delete = False
    verbose_name = _("AI Evaluation")
    verbose_name_plural = _("AI Evaluations")
    fields = [
        'overall_score', 'ats_score', 'grammar_score', 
        'keyword_score', 'completeness_score', 'summary', 
        'strengths', 'weaknesses', 'missing_skills', 
        'recommended_roles', 'analysis_status'
    ]
    readonly_fields = fields


class ResumeActivityInline(admin.TabularInline):
    """
    Inlines User auditable interaction histories inside the Resume details panel.
    """
    model = ResumeActivity
    extra = 0
    can_delete = False
    readonly_fields = ['action', 'description', 'created_at']


class ResumeAdmin(admin.ModelAdmin):
    """
    Admin control board for Resume records.
    """
    list_display = [
        'title', 'user_email', 'file_size_formatted', 'file_type', 
        'resume_version', 'processing_status', 'get_analysis_status', 
        'is_default', 'created_at', 'download_file_action'
    ]
    
    list_filter = ['file_type', 'processing_status', 'is_default', 'created_at']
    search_fields = ['title', 'original_filename', 'user__email', 'user__first_name', 'user__last_name']
    inlines = [ResumeAnalysisInline, ResumeActivityInline]
    ordering = ['-created_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _("User Email")

    def file_size_formatted(self, obj):
        return f"{round(obj.file_size / 1024, 1)} KB"
    file_size_formatted.short_description = _("Size")

    def get_analysis_status(self, obj):
        if hasattr(obj, 'analysis'):
            return obj.analysis.analysis_status
        return _("N/A")
    get_analysis_status.short_description = _("Analysis Status")

    def download_file_action(self, obj):
        """
        Renders an HTML link allowing administrator staff to download the file directly.
        """
        if obj.file:
            return mark_safe(
                f'<a href="{obj.file.url}" target="_blank" download style="color: #6366F1; font-weight: bold;">'
                f'{_("Download")}</a>'
            )
        return _("No File")
    download_file_action.short_description = _("Download File")


class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'points', 'category', 'badge_icon']
    list_filter = ['category', 'points']
    search_fields = ['title', 'description']


admin.site.register(Resume, ResumeAdmin)
admin.site.register(ResumeActivity)
