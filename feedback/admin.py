from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    InterviewEvaluation,
    TechnicalEvaluation,
    CommunicationEvaluation,
    HRBehaviorEvaluation,
    OverallEvaluation,
    ImprovementSuggestion,
    RecommendedResource,
    EvaluationHistory
)

class ImprovementSuggestionInline(admin.TabularInline):
    model = ImprovementSuggestion
    extra = 1
    fields = ['category', 'title', 'description', 'priority']


class RecommendedResourceInline(admin.TabularInline):
    model = RecommendedResource
    extra = 1
    fields = ['title', 'type', 'url', 'description']


class EvaluationHistoryInline(admin.TabularInline):
    model = EvaluationHistory
    extra = 0
    can_delete = False
    readonly_fields = ['action', 'description', 'performed_at']
    ordering = ['-performed_at']


class InterviewEvaluationAdmin(admin.ModelAdmin):
    """
    Main evaluation dashboard detailing session properties, inline suggestions,
    inline reference links, and audit history logs.
    """
    list_display = [
        'id', 'uuid', 'interview', 'user', 'evaluation_status', 'get_overall_score', 
        'get_overall_rating', 'evaluated_at', 'created_at'
    ]
    list_filter = [
        'evaluation_status', 'overall_evaluation__overall_rating', 'created_at'
    ]
    search_fields = [
        'interview__title', 'user__email', 'user__first_name', 'user__last_name', 'uuid'
    ]
    inlines = [ImprovementSuggestionInline, RecommendedResourceInline, EvaluationHistoryInline]
    ordering = ['-created_at']

    def get_overall_score(self, obj):
        if hasattr(obj, 'overall_evaluation'):
            return obj.overall_evaluation.overall_score
        return "-"
    get_overall_score.short_description = _("Overall Score")

    def get_overall_rating(self, obj):
        if hasattr(obj, 'overall_evaluation'):
            return obj.overall_evaluation.overall_rating
        return "-"
    get_overall_rating.short_description = _("Overall Rating")


admin.site.register(InterviewEvaluation, InterviewEvaluationAdmin)
admin.site.register(TechnicalEvaluation)
admin.site.register(CommunicationEvaluation)
admin.site.register(HRBehaviorEvaluation)
admin.site.register(OverallEvaluation)
admin.site.register(ImprovementSuggestion)
admin.site.register(RecommendedResource)
admin.site.register(EvaluationHistory)
