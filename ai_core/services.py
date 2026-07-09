from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import AIProvider, AIModel, AIRequestLog, AIUsageStatistics
from .constants import STATUS_SUCCESS, STATUS_FAILED

class AIService:
    """
    Service interface class implementing placeholder signatures for dynamic request routing,
    token estimation, and request logging.
    """

    @classmethod
    def initialize_provider(cls, provider_id: int) -> bool:
        """
        Placeholder: Initializes connection credentials to specific cloud/local API providers.
        """
        try:
            provider = AIProvider.objects.get(pk=provider_id, is_active=True)
            return True
        except AIProvider.DoesNotExist:
            return False

    @classmethod
    def switch_provider(cls, provider_id: int) -> AIProvider:
        """
        Placeholder: Switches the system's default LLM/embedding providers.
        """
        try:
            target = AIProvider.objects.get(pk=provider_id)
        except AIProvider.DoesNotExist:
            raise ValidationError("Target provider not found.")

        with transaction.atomic():
            AIProvider.objects.all().update(is_default=False)
            target.is_default = True
            target.save()

        return target

    @classmethod
    def route_request(cls, request_type: str, prompt: str, user=None) -> dict:
        """
        Placeholder: Route request to active provider endpoint (e.g. Ollama, Gemini).
        """
        provider = AIProvider.objects.filter(is_default=True, is_active=True).first()
        if not provider:
            provider = AIProvider.objects.filter(is_active=True).first()

        provider_name = provider.provider_name if provider else "Ollama"
        model_name = provider.model_name if provider else "llama3"

        # Mock successful result
        return {
            "provider": provider_name,
            "model": model_name,
            "response": f"Mock routed response for request type '{request_type}' with prompt: '{prompt}'",
            "token_usage": len(prompt.split()) * 2
        }

    @classmethod
    def log_request(cls, user, module_name: str, request_type: str, provider: str, model: str,
                    prompt_length: int, response_length: int, execution_time: float,
                    token_usage: int, request_status: str, error_message: str = "") -> AIRequestLog:
        """
        Action: Create record inside AIRequestLog, and update AIUsageStatistics indicators.
        """
        with transaction.atomic():
            log_item = AIRequestLog.objects.create(
                user=user,
                module_name=module_name,
                request_type=request_type,
                provider=provider,
                model=model,
                prompt_length=prompt_length,
                response_length=response_length,
                execution_time=execution_time,
                token_usage=token_usage,
                request_status=request_status,
                error_message=error_message
            )

            # Update User statistics
            if user:
                stats, created = AIUsageStatistics.objects.get_or_create(user=user)
                
                # Update counters
                stats.total_requests += 1
                if request_type == 'Embedding':
                    stats.embedding_requests += 1
                elif request_type == 'Speech':
                    stats.whisper_requests += 1
                else:
                    stats.llm_requests += 1

                # Calculate cumulative average response time
                current_total = stats.total_requests
                if current_total > 1:
                    stats.average_response_time = (
                        (stats.average_response_time * (current_total - 1) + execution_time) / current_total
                    )
                else:
                    stats.average_response_time = execution_time

                stats.save()

        return log_item

    @classmethod
    def validate_provider(cls, provider_name: str) -> bool:
        """
        Placeholder: Verifies API key validity or URL connection accessibility.
        """
        return provider_name in ['Ollama', 'Gemini', 'OpenAI']

    @classmethod
    def estimate_tokens(cls, prompt: str) -> int:
        """
        Placeholder: Estimates model token length for prompts.
        """
        return len(str(prompt).split()) * 2

    @classmethod
    def check_model_health(cls, model_id: int) -> str:
        """
        Placeholder: Pings remote models to verify availability.
        """
        try:
            model = AIModel.objects.get(pk=model_id)
            return "Healthy" if model.status == "Active" else "Offline"
        except AIModel.DoesNotExist:
            return "Unknown"
