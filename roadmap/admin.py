from django.contrib import admin
from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder,
    RoadmapPathway,
    RoadmapMilestone
)

class RoadmapModuleInline(admin.TabularInline):
    model = RoadmapModule
    extra = 1
    fields = ['title', 'module_order', 'estimated_hours', 'module_type']


class LearningResourceInline(admin.TabularInline):
    model = LearningResource
    extra = 1
    fields = ['title', 'resource_type', 'provider', 'url', 'duration', 'is_free']


class ModuleProgressInline(admin.TabularInline):
    model = ModuleProgress
    extra = 0
    can_delete = False
    readonly_fields = ['roadmap_module', 'is_completed', 'completion_date', 'notes']


class RoadmapMilestoneInline(admin.TabularInline):
    model = RoadmapMilestone
    extra = 0
    fields = ['milestone_number', 'title', 'difficulty_tag', 'estimated_hours', 'is_completed', 'progress_percent']
    readonly_fields = ['milestone_number', 'title', 'difficulty_tag', 'estimated_hours']


class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'career_path', 'estimated_duration', 'total_modules', 'difficulty', 'is_active', 'created_at']
    list_filter = ['career_path', 'difficulty', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [RoadmapModuleInline]
    ordering = ['title']


class RoadmapModuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'roadmap', 'module_order', 'estimated_hours', 'module_type']
    list_filter = ['roadmap', 'module_type']
    search_fields = ['title', 'description']
    inlines = [LearningResourceInline]
    ordering = ['roadmap', 'module_order']


class UserRoadmapAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'roadmap', 'progress_percentage', 'completed_modules', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'roadmap__title']
    inlines = [ModuleProgressInline]
    ordering = ['-started_at']


class RoadmapPathwayAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'pathway_title', 'inferred_starting_level', 'overall_readiness_estimate_percent', 'created_at']
    list_filter = ['inferred_starting_level', 'created_at']
    search_fields = ['user__email', 'pathway_title', 'user_interest_text']
    inlines = [RoadmapMilestoneInline]
    readonly_fields = ['pathway_title', 'inferred_starting_level', 'inferred_level_reason', 'overall_readiness_estimate_percent', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        # Pathways are generated via API, not manually created in admin
        return False


class RoadmapMilestoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'pathway', 'milestone_number', 'title', 'difficulty_tag', 'estimated_hours', 'is_completed', 'progress_percent']
    list_filter = ['pathway__inferred_starting_level', 'difficulty_tag', 'is_completed']
    search_fields = ['title', 'description', 'pathway__pathway_title']
    readonly_fields = ['milestone_number', 'title', 'difficulty_tag', 'description', 'why_it_matters', 'estimated_hours', 'key_topics', 'created_at', 'updated_at']
    ordering = ['pathway', 'milestone_number']


admin.site.register(CareerPath)
admin.site.register(Roadmap, RoadmapAdmin)
admin.site.register(RoadmapModule, RoadmapModuleAdmin)
admin.site.register(LearningResource)
admin.site.register(UserRoadmap, UserRoadmapAdmin)
admin.site.register(ModuleProgress)
admin.site.register(LearningReminder)
admin.site.register(RoadmapPathway, RoadmapPathwayAdmin)
admin.site.register(RoadmapMilestone, RoadmapMilestoneAdmin)
