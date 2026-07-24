import os
import time
import json
import logging
import urllib.error
import socket
from django.utils import timezone

from ai_core.services import AIService
from ai_core.models import AIProvider
from .exceptions import AITimeoutError, AIParsingError, AIProviderError
from .circuit_breaker import CircuitBreaker
from .metrics import MetricsCollector

logger = logging.getLogger(__name__)
tracker_logger = logging.getLogger("ai_generation_tracker")

# Configs
AI_GENERATION_TIMEOUT_SECONDS = int(os.getenv("AI_GENERATION_TIMEOUT_SECONDS", 10))

def is_timeout_exception(e) -> bool:
    """Helper to detect timeout exceptions from urllib or socket."""
    if isinstance(e, (socket.timeout, TimeoutError)):
        return True
    if isinstance(e, urllib.error.URLError):
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            return True
        if "timed out" in str(e.reason).lower() or "timeout" in str(e.reason).lower():
            return True
    if "timed out" in str(e).lower() or "timeout" in str(e).lower():
        return True
    return False

def execute_ai_call_with_retry(
    request_type: str,
    prompt: str,
    user,
    feature: str,
    session_id: str,
    user_id: str,
    metadata: dict,
    validator_func,
    fallback_tier: int = 2
) -> dict:
    """
    Executes the Tier 1 AI request with custom timeout (default 10s), 
    exactly 1 retry (5s timeout) on timeout, circuit breaker checks/updates, 
    structured log emission, and metrics tracking.
    """
    # 1. Resolve Provider
    provider_obj = AIProvider.objects.filter(is_default=True, is_active=True).first()
    if not provider_obj:
        provider_obj = AIProvider.objects.filter(is_active=True).first()
    provider_name = provider_obj.provider_name if provider_obj else "Gemini"

    breaker = CircuitBreaker(provider_name)
    start_time = time.time()
    latency_ms = 0
    failure_reason = None
    res_dict = None
    parsed_json = None

    # 2. Check Circuit Breaker
    if not breaker.allow_request():
        latency_ms = int((time.time() - start_time) * 1000)
        failure_reason = "circuit_open"
        log_data = {
            "tier_reached": fallback_tier,
            "failure_reason": failure_reason,
            "latency_ms": latency_ms,
            "role": metadata.get("role"),
            "company": metadata.get("company"),
            "difficulty": metadata.get("difficulty"),
            "mode": metadata.get("mode"),
            "session_id": str(session_id),
            "user_id": str(user_id)
        }
        if "language" in metadata:
            log_data["language"] = metadata["language"]
        
        tracker_logger.warning(json.dumps(log_data))
        MetricsCollector.increment_counter("generation_tier_result_total", {"tier": str(fallback_tier), "failure_reason": failure_reason, "feature": feature})
        MetricsCollector.record_histogram("generation_latency_ms", latency_ms, {"tier": str(fallback_tier), "feature": feature})
        raise AIProviderError("Circuit breaker is open. Shunting request directly to fallback.")

    try:
        # Attempt 1
        try:
            res_dict = AIService.route_request(request_type, prompt, user, timeout=AI_GENERATION_TIMEOUT_SECONDS)
        except Exception as e:
            if is_timeout_exception(e):
                logger.warning(f"AI Provider '{provider_name}' timed out on Attempt 1. Retrying once with 5s timeout...")
                # Attempt 2 (Retry)
                try:
                    res_dict = AIService.route_request(request_type, prompt, user, timeout=5)
                except Exception as retry_e:
                    if is_timeout_exception(retry_e):
                        raise AITimeoutError("AI call timed out on retry attempt.")
                    else:
                        raise AIProviderError(str(retry_e))
            else:
                raise AIProviderError(str(e))

        # 3. Parse and Validate Response
        raw_response = res_dict.get("response", "").strip() if res_dict else ""
        try:
            parsed_json = validator_func(raw_response)
        except Exception as parse_err:
            raise AIParsingError(f"Response validation failed: {str(parse_err)}")

        # Success path
        breaker.record_success()
        latency_ms = int((time.time() - start_time) * 1000)
        log_data = {
            "tier_reached": 1,
            "failure_reason": None,
            "latency_ms": latency_ms,
            "role": metadata.get("role"),
            "company": metadata.get("company"),
            "difficulty": metadata.get("difficulty"),
            "mode": metadata.get("mode"),
            "session_id": str(session_id),
            "user_id": str(user_id)
        }
        if "language" in metadata:
            log_data["language"] = metadata["language"]

        tracker_logger.info(json.dumps(log_data))
        MetricsCollector.increment_counter("generation_tier_result_total", {"tier": "1", "failure_reason": "none", "feature": feature})
        MetricsCollector.record_histogram("generation_latency_ms", latency_ms, {"tier": "1", "feature": feature})
        return parsed_json

    except Exception as e:
        breaker.record_failure()
        latency_ms = int((time.time() - start_time) * 1000)

        if isinstance(e, AITimeoutError):
            failure_reason = "timeout"
        elif isinstance(e, AIParsingError):
            failure_reason = "parse_error"
        else:
            failure_reason = "provider_error"

        # Log transition to fallback tier
        log_data = {
            "tier_reached": fallback_tier,
            "failure_reason": failure_reason,
            "latency_ms": latency_ms,
            "role": metadata.get("role"),
            "company": metadata.get("company"),
            "difficulty": metadata.get("difficulty"),
            "mode": metadata.get("mode"),
            "session_id": str(session_id),
            "user_id": str(user_id)
        }
        if "language" in metadata:
            log_data["language"] = metadata["language"]

        tracker_logger.warning(json.dumps(log_data))
        MetricsCollector.increment_counter("generation_tier_result_total", {"tier": str(fallback_tier), "failure_reason": failure_reason, "feature": feature})
        MetricsCollector.record_histogram("generation_latency_ms", latency_ms, {"tier": str(fallback_tier), "feature": feature})
        raise e
