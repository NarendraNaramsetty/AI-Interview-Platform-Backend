from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    CodingCategory,
    CodingProblem,
    TestCase,
    CodeSubmission,
    CodingScore,
    CodingHistory,
    FavoriteProblem
)

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1
    fields = ['input_data', 'expected_output', 'is_sample', 'is_hidden']


class CodingScoreInline(admin.StackedInline):
    model = CodingScore
    extra = 0
    can_delete = False
    readonly_fields = ['score', 'percentage', 'ranking_points', 'feedback_placeholder']


class CodingHistoryInline(admin.TabularInline):
    model = CodingHistory
    extra = 0
    can_delete = False
    readonly_fields = ['action', 'description', 'timestamp']
    ordering = ['-timestamp']


class CodingProblemAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'slug', 'difficulty', 'category', 
        'company', 'points', 'is_active', 'created_at'
    ]
    list_filter = ['difficulty', 'category', 'company', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'problem_statement', 'tags']
    inlines = [TestCaseInline]
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['category', 'title']


class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'uuid', 'user', 'problem', 'programming_language', 
        'status', 'passed_test_cases', 'total_test_cases', 'created_at'
    ]
    list_filter = ['status', 'programming_language', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'problem__title', 'uuid']
    inlines = [CodingScoreInline, CodingHistoryInline]
    ordering = ['-created_at']


admin.site.register(CodingCategory)
admin.site.register(CodingProblem, CodingProblemAdmin)
admin.site.register(TestCase)
admin.site.register(CodeSubmission, CodeSubmissionAdmin)
admin.site.register(CodingScore)
admin.site.register(CodingHistory)
admin.site.register(FavoriteProblem)
