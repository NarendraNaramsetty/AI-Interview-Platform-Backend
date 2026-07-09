import urllib.request
import json
import logging
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import AIProvider, AIModel, AIRequestLog, AIUsageStatistics
from .constants import STATUS_SUCCESS, STATUS_FAILED
from .config import GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

def _execute_http_post(url, headers, payload, timeout=30):
    # Enforce standard browser User-Agent to prevent Cloudflare blocks (Error 1010)
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logger.error(f"HTTP Post request failed to {url}: {str(e)}")
        if hasattr(e, 'read'):
            try:
                err_body = e.read().decode('utf-8')
                logger.error(f"Error response body: {err_body}")
                try:
                    err_json = json.loads(err_body)
                    return {"error": err_json.get("error", err_json), "details": err_body}
                except Exception:
                    return {"error": str(e), "details": err_body}
            except Exception:
                pass
        raise e

class AIService:
    """
    Service interface class implementing dynamic request routing,
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
        Route request to active provider endpoint (e.g. Ollama, Gemini, Groq) using live APIs.
        """
        # Initialize default provider configurations in database if none exist
        if not AIProvider.objects.exists():
            try:
                with transaction.atomic():
                    gemini_prov = AIProvider.objects.create(
                        provider_name='Gemini',
                        provider_type='Cloud',
                        base_url='https://generativelanguage.googleapis.com',
                        model_name='gemini-2.5-flash',
                        is_default=True,
                        is_active=True
                    )
                    AIModel.objects.create(
                        provider=gemini_prov,
                        model_name='gemini-2.5-flash',
                        model_type='Chat',
                        status='Active'
                    )
                    
                    groq_prov = AIProvider.objects.create(
                        provider_name='Groq',
                        provider_type='Cloud',
                        base_url='https://api.groq.com',
                        model_name='llama-3.1-8b-instant',
                        is_default=False,
                        is_active=True
                    )
                    AIModel.objects.create(
                        provider=groq_prov,
                        model_name='llama-3.1-8b-instant',
                        model_type='Chat',
                        status='Active'
                    )
                    AIModel.objects.create(
                        provider=groq_prov,
                        model_name='llama-3.3-70b-versatile',
                        model_type='Chat',
                        status='Active'
                    )
            except Exception as dbe:
                logger.error(f"Failed to populate default AI providers: {str(dbe)}")

        # Resolve default provider
        provider = AIProvider.objects.filter(is_default=True, is_active=True).first()
        if not provider:
            provider = AIProvider.objects.filter(is_active=True).first()

        provider_name = provider.provider_name if provider else "Gemini"
        model_name = provider.model_name if provider else "gemini-2.5-flash"
        base_url = provider.base_url if provider else ""
        timeout_val = provider.timeout if provider else 30

        # Override model name if empty
        if not model_name:
            if provider_name == 'Gemini':
                model_name = 'gemini-2.5-flash'
            elif provider_name == 'Groq':
                model_name = 'llama-3.1-8b-instant'
            else:
                model_name = 'llama3'

        response_text = ""
        try:
            if provider_name == 'Gemini':
                api_key = GEMINI_API_KEY
                if not api_key:
                    raise ValueError("Gemini API key is not configured.")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
                res_data = _execute_http_post(url, headers, payload, timeout_val)
                if "error" in res_data:
                    err_obj = res_data["error"]
                    if isinstance(err_obj, dict):
                        err_msg = err_obj.get("message", json.dumps(err_obj))
                    else:
                        err_msg = f"{err_obj}. Details: {res_data.get('details', '')}"
                    raise Exception(f"Gemini API Error: {err_msg}")
                response_text = res_data['candidates'][0]['content']['parts'][0]['text']

            elif provider_name == 'Groq':
                api_key = GROQ_API_KEY
                if not api_key:
                    raise ValueError("Groq API key is not configured.")
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}]
                }
                res_data = _execute_http_post(url, headers, payload, timeout_val)
                if "error" in res_data:
                    err_obj = res_data["error"]
                    if isinstance(err_obj, dict):
                        err_msg = err_obj.get("message", json.dumps(err_obj))
                    else:
                        err_msg = f"{err_obj}. Details: {res_data.get('details', '')}"
                    raise Exception(f"Groq API Error: {err_msg}")
                response_text = res_data['choices'][0]['message']['content']

            elif provider_name == 'OpenAI':
                api_key = OPENAI_API_KEY
                if not api_key:
                    raise ValueError("OpenAI API key is not configured.")
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}]
                }
                res_data = _execute_http_post(url, headers, payload, timeout_val)
                response_text = res_data['choices'][0]['message']['content']

            elif provider_name == 'Ollama':
                url = f"{base_url or 'http://localhost:11434'}/api/generate"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False
                }
                res_data = _execute_http_post(url, headers, payload, timeout_val)
                response_text = res_data['response']

            else:
                raise ValueError(f"Unsupported AI Provider: {provider_name}")

        except Exception as e:
            logger.error(f"Error in route_request: {str(e)}")
            response_text = f"[AI Service Connection Error: {str(e)}]\n\nFallback: Ready to conduct technical prep simulations. Let's start with your background and target tech stack."

        return {
            "provider": provider_name,
            "model": model_name,
            "response": response_text,
            "token_usage": (len(prompt.split()) + len(response_text.split())) * 2
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
