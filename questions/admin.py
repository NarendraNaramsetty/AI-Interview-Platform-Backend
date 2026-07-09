from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    QuestionCategory,
    Company,
    JobRole,
    Topic,
    QuestionTag,
    InterviewQuestion,
    QuestionAttachment,
    QuestionHistory
)

class QuestionAttachmentInline(admin.TabularInline):
    model = QuestionAttachment
    extra = 1
    fields = ['file', 'file_type']
    readonly_fields = ['file_type']


class QuestionHistoryInline(admin.TabularInline):
    model = QuestionHistory
    extra = 0
    can_delete = False
    readonly_fields = ['action', 'description', 'performed_by', 'timestamp']
    ordering = ['-timestamp']


class InterviewQuestionAdmin(admin.ModelAdmin):
    """
    Main admin interface displaying question descriptors, nested attachments, and histories.
    """
    list_display = [
        'get_short_text', 'category', 'topic', 'difficulty', 
        'expected_duration', 'answer_type', 'is_active', 'created_at'
    ]
    list_filter = ['category', 'difficulty', 'answer_type', 'is_active', 'created_at']
    search_fields = ['question', 'short_description', 'expected_answer', 'explanation']
    inlines = [QuestionAttachmentInline, QuestionHistoryInline]
    ordering = ['-created_at']

    def get_short_text(self, obj):
        if obj.short_description:
            return obj.short_description
        return f"{obj.question[:50]}..."
    get_short_text.short_description = _("Question / Description")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(QuestionCategory)
admin.site.register(Company)
admin.site.register(JobRole)
admin.site.register(Topic)
admin.site.register(QuestionTag)
admin.site.register(InterviewQuestion, InterviewQuestionAdmin)
admin.site.register(QuestionHistory)
