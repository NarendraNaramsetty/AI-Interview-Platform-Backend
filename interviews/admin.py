from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewProgress,
    InterviewResult,
    InterviewTimeline
)

class InterviewQuestionInline(admin.TabularInline):
    model = InterviewQuestion
    extra = 0
    ordering = ['sequence_number']


class InterviewAnswerInline(admin.TabularInline):
    model = InterviewAnswer
    extra = 0
    readonly_fields = ['question', 'answer_text', 'answer_type', 'audio_file', 'answer_duration', 'submitted_at']
    can_delete = False


class InterviewProgressInline(admin.StackedInline):
    model = InterviewProgress
    can_delete = False
    verbose_name = _("Progress Parameters")
    verbose_name_plural = _("Progress Parameters")


class InterviewResultInline(admin.StackedInline):
    model = InterviewResult
    can_delete = False
    verbose_name = _("AI Scoring Result")
    verbose_name_plural = _("AI Scoring Results")


class InterviewTimelineInline(admin.TabularInline):
    model = InterviewTimeline
    extra = 0
    readonly_fields = ['action', 'description', 'timestamp']
    can_delete = False
    ordering = ['timestamp']


class InterviewSessionAdmin(admin.ModelAdmin):
    """
    Main portal admin view managing session lifecycle, inlining questions, answers, and evaluations.
    """
    list_display = [
        'title', 'user_email', 'target_role', 'target_company', 
        'interview_type', 'difficulty', 'interview_mode', 'status', 'created_at'
    ]
    list_filter = ['interview_type', 'difficulty', 'interview_mode', 'status', 'created_at']
    search_fields = ['title', 'target_role', 'target_company', 'user__email', 'user__first_name']
    inlines = [
        InterviewQuestionInline, 
        InterviewAnswerInline, 
        InterviewProgressInline, 
        InterviewResultInline, 
        InterviewTimelineInline
    ]
    ordering = ['-created_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _("User Email")


admin.site.register(InterviewSession, InterviewSessionAdmin)
admin.site.register(InterviewQuestion)
admin.site.register(InterviewAnswer)
admin.site.register(InterviewTimeline)
