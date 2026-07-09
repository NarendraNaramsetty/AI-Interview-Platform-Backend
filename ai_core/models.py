import uuid
from django.db import models
from django.conf import settings
from .constants import (
    PROVIDER_CHOICES,
    PROVIDER_OLLAMA,
    MODEL_TYPE_CHOICES,
    MODEL_TYPE_CHAT,
    REQ_TYPE_CHOICES,
    REQ_CHAT,
    STATUS_CHOICES,
    STATUS_SUCCESS
)

class AIProvider(models.Model):
    """
    Registry of integrated AI platform providers (Ollama, Gemini, OpenAI).
    """
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    provider_name = models.CharField(max_length=100, choices=PROVIDER_CHOICES, unique=True)
    provider_type = models.CharField(max_length=50)  # e.g., Local, Cloud
    base_url = models.URLField(blank=True)
    model_name = models.CharField(max_length=150)
    api_key_reference = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    max_tokens = models.IntegerField(default=2048)
    timeout = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider_name']
        verbose_name = "AI Provider"
        verbose_name_plural = "AI Providers"

    def __str__(self):
        return f"{self.provider_name} ({self.model_name})"


class AIModel(models.Model):
    """
    Details models catalog specifications.
    """
    id = models.BigAutoField(primary_key=True)
    provider = models.ForeignKey(
        AIProvider,
        on_delete=models.CASCADE,
        related_name='models'
    )
    model_name = models.CharField(max_length=150)
    model_version = models.CharField(max_length=50, blank=True)
    model_type = models.CharField(
        max_length=50,
        choices=MODEL_TYPE_CHOICES,
        default=MODEL_TYPE_CHAT
    )
    status = models.CharField(max_length=50, default='Active')
    context_window = models.IntegerField(default=4096)
    supports_streaming = models.BooleanField(default=True)
    supports_function_calling = models.BooleanField(default=False)

    class Meta:
        ordering = ['model_name']
        verbose_name = "AI Model"
        verbose_name_plural = "AI Models"

    def __str__(self):
        return f"{self.model_name} ({self.model_type})"


class AIRequestLog(models.Model):
    """
    Logs metadata about requests to track pricing, latency, and errors.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_request_logs'
    )
    module_name = models.CharField(max_length=100)
    request_type = models.CharField(
        max_length=100,
        choices=REQ_TYPE_CHOICES,
        default=REQ_CHAT
    )
    provider = models.CharField(max_length=100)
    model = models.CharField(max_length=150)
    prompt_length = models.IntegerField(default=0)
    response_length = models.IntegerField(default=0)
    execution_time = models.FloatField(default=0.0)  # in seconds
    token_usage = models.IntegerField(default=0)
    request_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_SUCCESS
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "AI Request Log"
        verbose_name_plural = "AI Request Logs"

    def __str__(self):
        return f"Log {self.id} - User: {self.user.email if self.user else 'Anon'} - Provider: {self.provider}"


class AIConfiguration(models.Model):
    """
    Key-Value options for dynamic AI prompts configuration.
    """
    id = models.BigAutoField(primary_key=True)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['key']
        verbose_name = "AI Configuration"
        verbose_name_plural = "AI Configurations"

    def __str__(self):
        return self.key


class AIUsageStatistics(models.Model):
    """
    User stats tracking total requests.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_statistics'
    )
    total_requests = models.IntegerField(default=0)
    embedding_requests = models.IntegerField(default=0)
    llm_requests = models.IntegerField(default=0)
    whisper_requests = models.IntegerField(default=0)
    qdrant_searches = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Usage Statistics"
        verbose_name_plural = "AI Usage Statistics"

    def __str__(self):
        return f"AI Stats for {self.user.email}"
