from django.contrib import admin
from .models import (
    AIProvider,
    AIModel,
    AIRequestLog,
    AIConfiguration,
    AIUsageStatistics
)

class AIModelInline(admin.TabularInline):
    model = AIModel
    extra = 1
    fields = ['model_name', 'model_type', 'status', 'context_window', 'supports_streaming']


class AIProviderAdmin(admin.ModelAdmin):
    list_display = ['id', 'provider_name', 'provider_type', 'model_name', 'is_default', 'is_active', 'timeout', 'created_at']
    list_filter = ['provider_type', 'is_default', 'is_active']
    search_fields = ['provider_name', 'model_name']
    inlines = [AIModelInline]


class AIModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'provider', 'model_name', 'model_type', 'status', 'context_window']
    list_filter = ['model_type', 'status']
    search_fields = ['model_name', 'provider__provider_name']


class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'module_name', 'request_type', 'provider', 'model', 'execution_time', 'token_usage', 'request_status', 'created_at']
    list_filter = ['request_status', 'request_type', 'created_at']
    search_fields = ['user__email', 'provider', 'model', 'module_name', 'error_message']


class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = ['id', 'key', 'value', 'is_active']
    list_filter = ['is_active']
    search_fields = ['key', 'value', 'description']


class AIUsageStatisticsAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_requests', 'embedding_requests', 'llm_requests', 'whisper_requests', 'average_response_time']
    search_fields = ['user__email']


admin.site.register(AIProvider, AIProviderAdmin)
admin.site.register(AIModel, AIModelAdmin)
admin.site.register(AIRequestLog, AIRequestLogAdmin)
admin.site.register(AIConfiguration, AIConfigurationAdmin)
admin.site.register(AIUsageStatistics, AIUsageStatisticsAdmin)
