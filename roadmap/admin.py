from django.contrib import admin
from .models import (
    CareerPath,
    Roadmap,
    RoadmapModule,
    LearningResource,
    UserRoadmap,
    ModuleProgress,
    LearningReminder
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


admin.site.register(CareerPath)
admin.site.register(Roadmap, RoadmapAdmin)
admin.site.register(RoadmapModule, RoadmapModuleAdmin)
admin.site.register(LearningResource)
admin.site.register(UserRoadmap, UserRoadmapAdmin)
admin.site.register(ModuleProgress)
admin.site.register(LearningReminder)
