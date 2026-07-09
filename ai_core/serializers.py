from rest_framework import serializers
from .models import (
    AIProvider,
    AIModel,
    AIRequestLog,
    AIConfiguration,
    AIUsageStatistics
)

class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = ['id', 'uuid', 'provider_name', 'provider_type', 'base_url', 'model_name', 'api_key_reference', 'is_default', 'is_active', 'max_tokens', 'timeout', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uuid', 'created_at', 'updated_at']


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = ['id', 'provider', 'model_name', 'model_version', 'model_type', 'status', 'context_window', 'supports_streaming', 'supports_function_calling']
        read_only_fields = ['id']


class AIRequestLogSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AIRequestLog
        fields = ['id', 'user', 'email', 'module_name', 'request_type', 'provider', 'model', 'prompt_length', 'response_length', 'execution_time', 'token_usage', 'request_status', 'error_message', 'created_at']
        read_only_fields = fields


class AIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConfiguration
        fields = ['id', 'key', 'value', 'description', 'is_active']
        read_only_fields = ['id']


class AIUsageStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIUsageStatistics
        fields = ['id', 'user', 'total_requests', 'embedding_requests', 'llm_requests', 'whisper_requests', 'qdrant_searches', 'average_response_time', 'created_at', 'updated_at']
        read_only_fields = fields
