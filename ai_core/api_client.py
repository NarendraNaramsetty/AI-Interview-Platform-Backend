"""
API Key Rotation & Fallback System

This module provides a reusable wrapper for managing multiple API keys per provider
with automatic rotation and fallback on rate-limiting. Supports Gemini and Groq.

Features:
- Dynamic API key loading from .env (no hardcoded limits)
- Automatic key rotation on rate-limit (429) errors
- Proactive key switching based on remaining rate-limit
- In-memory cooldown for exhausted keys
- Comprehensive logging for debugging
- Framework-agnostic implementation
"""

import os
import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported AI providers."""
    GEMINI = "gemini"
    GROQ = "groq"


class RateLimitError(Exception):
    """Raised when API rate limit is hit."""
    pass


class AllKeysExhaustedError(Exception):
    """Raised when all API keys for a provider are exhausted."""
    pass


@dataclass
class APIKey:
    """Represents a single API key with metadata."""
    key: str
    index: int
    provider: ProviderType
    last_used: Optional[datetime] = None
    last_rate_limited: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    use_count: int = 0
    error_count: int = 0
    
    def is_on_cooldown(self) -> bool:
        """Check if key is currently on cooldown."""
        if self.cooldown_until is None:
            return False
        return datetime.now() < self.cooldown_until
    
    def mark_rate_limited(self, cooldown_seconds: int = 60):
        """Mark key as rate-limited with cooldown period."""
        now = datetime.now()
        self.last_rate_limited = now
        self.cooldown_until = now + timedelta(seconds=cooldown_seconds)
        self.error_count += 1
        logger.warning(
            f"Key #{self.index} ({self.provider.value}) rate-limited. "
            f"Cooldown until {self.cooldown_until.isoformat()}"
        )
    
    def mark_used(self):
        """Record successful use of this key."""
        self.last_used = datetime.now()
        self.use_count += 1


@dataclass
class RateLimitInfo:
    """Information about rate limits from provider response."""
    remaining_requests: Optional[int] = None
    remaining_tokens: Optional[int] = None
    limit_requests: Optional[int] = None
    limit_tokens: Optional[int] = None
    reset_time: Optional[str] = None
    
    def should_switch_key(self, threshold_requests: int = 10, threshold_tokens: int = 1000) -> bool:
        """
        Check if we should proactively switch to next key based on thresholds.
        
        Args:
            threshold_requests: Switch if remaining requests <= this value
            threshold_tokens: Switch if remaining tokens <= this value
        """
        if self.remaining_requests is not None and self.remaining_requests <= threshold_requests:
            return True
        if self.remaining_tokens is not None and self.remaining_tokens <= threshold_tokens:
            return True
        return False


class APIKeyManager:
    """
    Manages multiple API keys per provider with rotation, fallback, and cooldown.
    
    Usage:
        manager = APIKeyManager()
        try:
            response = manager.call_provider(
                provider=ProviderType.GEMINI,
                url="https://...",
                headers={...},
                payload={...}
            )
        except AllKeysExhaustedError:
            # All keys are exhausted
            handle_exhaustion()
    """
    
    # In-memory storage of keys and their metadata
    _keys: Dict[ProviderType, List[APIKey]] = {}
    _call_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __init__(self):
        """Initialize key manager and load keys from environment."""
        self._keys = {}
        self._call_history = []
        self._load_keys_from_env()
        self._log_loaded_keys()
    
    @staticmethod
    def _load_keys_from_env() -> None:
        """
        Dynamically load API keys from environment variables.
        Scans for patterns: PROVIDER_API_KEY, PROVIDER_API_KEY2, etc.
        Handles both standard and case-variant names (e.g., Gemini_API_KEY, GEMINI_API_KEY).
        """
        # Define provider patterns (order matters for matching)
        provider_patterns = {
            ProviderType.GEMINI: [
                'GEMINI_API_KEY',
                'Gemini_API_KEY',
                'gemini_api_key',
            ],
            ProviderType.GROQ: [
                'GROQ_API_KEY',
                'Groke_API_KEY',  # Note: Your .env uses "Groke" (typo?)
                'groq_api_key',
                'groke_api_key',
            ],
        }
        
        for provider, patterns in provider_patterns.items():
            keys = []
            base_names_found = set()
            
            # First, collect base pattern keys (no number suffix)
            for pattern in patterns:
                key_value = os.getenv(pattern)
                if key_value and pattern not in base_names_found:
                    keys.append(key_value)
                    base_names_found.add(pattern)
                    logger.debug(f"Loaded {provider.value.upper()} key from {pattern}")
            
            # Then, look for numbered variants (KEY2, KEY3, etc.)
            i = 2
            while i <= 10:  # Support up to 10 keys per provider
                found_variant = False
                for pattern in patterns:
                    # Build numbered variant (e.g., GEMINI_API_KEY2, Gemini_API_KEY2)
                    base = pattern.rsplit('_API_KEY', 1)[0] if '_API_KEY' in pattern else pattern
                    numbered_pattern = f"{base}_API_KEY{i}"
                    
                    key_value = os.getenv(numbered_pattern)
                    if key_value:
                        keys.append(key_value)
                        found_variant = True
                        logger.debug(f"Loaded {provider.value.upper()} key #{i} from {numbered_pattern}")
                        break  # Found for this number, move to next number
                
                if not found_variant:
                    break  # No more variants for this number
                i += 1
            
            if keys:
                APIKeyManager._keys[provider] = [
                    APIKey(key=k, index=idx, provider=provider)
                    for idx, k in enumerate(keys)
                ]
                logger.info(f"Loaded {len(keys)} key(s) for {provider.value.upper()}")
            else:
                APIKeyManager._keys[provider] = []
                logger.warning(f"No API keys found for {provider.value.upper()}")
    
    @staticmethod
    def _log_loaded_keys() -> None:
        """Log summary of loaded keys (showing indices, not actual keys)."""
        for provider, keys in APIKeyManager._keys.items():
            if keys:
                key_indices = ", ".join(str(k.index) for k in keys)
                logger.info(f"{provider.value.upper()}: {len(keys)} key(s) [indices: {key_indices}]")
    
    @staticmethod
    def get_available_keys(provider: ProviderType) -> List[APIKey]:
        """Get list of available (non-exhausted) keys for a provider."""
        if provider not in APIKeyManager._keys:
            return []
        
        keys = APIKeyManager._keys[provider]
        # Filter out keys on cooldown
        available = [k for k in keys if not k.is_on_cooldown()]
        
        if not available:
            logger.warning(
                f"All {provider.value.upper()} keys are on cooldown. "
                f"Keys: {[(k.index, k.cooldown_until) for k in keys if k.is_on_cooldown()]}"
            )
        
        return available
    
    @staticmethod
    def get_next_key(provider: ProviderType, exclude_indices: Optional[List[int]] = None) -> Optional[APIKey]:
        """
        Get the next available key for a provider.
        
        Args:
            provider: Provider to get key for
            exclude_indices: Key indices to skip
            
        Returns:
            Next available APIKey, or None if all exhausted
        """
        exclude_indices = exclude_indices or []
        available = APIKeyManager.get_available_keys(provider)
        
        for key in available:
            if key.index not in exclude_indices:
                return key
        
        return None
    
    @staticmethod
    def call_provider(
        provider: ProviderType,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        timeout: int = 30,
        max_retries: int = 3,
    ) -> Tuple[Any, Optional[RateLimitInfo], int]:
        """
        Make API call with automatic key rotation on rate-limit.
        
        Args:
            provider: Provider type (GEMINI or GROQ)
            url: API endpoint URL
            headers: Request headers (will add auth)
            payload: Request payload
            timeout: Request timeout in seconds
            max_retries: Maximum number of keys to try
            
        Returns:
            Tuple of (response_data, rate_limit_info, key_index_used)
            
        Raises:
            AllKeysExhaustedError: When all keys are exhausted
            Exception: For non-rate-limit errors
        """
        if provider not in APIKeyManager._keys:
            raise ValueError(f"Provider {provider.value} not supported or not configured")
        
        available_keys = APIKeyManager.get_available_keys(provider)
        if not available_keys:
            raise AllKeysExhaustedError(
                f"All API keys for {provider.value.upper()} are rate-limited or exhausted"
            )
        
        tried_indices = []
        last_error = None
        
        for attempt in range(min(max_retries, len(available_keys))):
            key = APIKeyManager.get_next_key(provider, exclude_indices=tried_indices)
            
            if key is None:
                break
            
            tried_indices.append(key.index)
            
            try:
                logger.info(
                    f"Attempt {attempt + 1}/{min(max_retries, len(available_keys))}: "
                    f"Using {provider.value.upper()} key #{key.index}"
                )
                
                # Make the API call
                response_data, headers_response = APIKeyManager._make_request(
                    url=url,
                    headers=headers,
                    payload=payload,
                    api_key=key.key,
                    provider=provider,
                    timeout=timeout,
                )
                
                # Parse rate limit info from response headers
                rate_limit_info = APIKeyManager._parse_rate_limit_headers(
                    headers_response, provider
                )
                
                # Check if we should proactively switch keys
                if rate_limit_info and rate_limit_info.should_switch_key():
                    logger.warning(
                        f"Rate limit approaching for {provider.value.upper()} key #{key.index}. "
                        f"Remaining: {rate_limit_info.remaining_requests} requests, "
                        f"{rate_limit_info.remaining_tokens} tokens"
                    )
                
                # Mark key as successfully used
                key.mark_used()
                
                # Record successful call
                APIKeyManager._record_call(
                    provider=provider,
                    key_index=key.index,
                    success=True,
                    rate_limit_info=rate_limit_info,
                )
                
                logger.info(
                    f"✓ Success with {provider.value.upper()} key #{key.index}. "
                    f"Total uses: {key.use_count}"
                )
                
                return response_data, rate_limit_info, key.index
            
            except RateLimitError as e:
                last_error = e
                logger.warning(
                    f"✗ Rate limit hit with {provider.value.upper()} key #{key.index}. "
                    f"Attempting next key..."
                )
                
                # Mark key as rate-limited with cooldown
                key.mark_rate_limited(cooldown_seconds=60)
                
                # Record failed call
                APIKeyManager._record_call(
                    provider=provider,
                    key_index=key.index,
                    success=False,
                    error=str(e),
                    rate_limit_info=None,
                )
                
                # Continue to next key
                continue
            
            except Exception as e:
                last_error = e
                logger.error(
                    f"✗ Error with {provider.value.upper()} key #{key.index}: {str(e)}"
                )
                
                key.error_count += 1
                
                # Record failed call
                APIKeyManager._record_call(
                    provider=provider,
                    key_index=key.index,
                    success=False,
                    error=str(e),
                    rate_limit_info=None,
                )
                
                # Re-raise non-rate-limit errors immediately
                raise
        
        # All keys exhausted
        error_msg = (
            f"All {provider.value.upper()} keys exhausted after {len(tried_indices)} attempts. "
            f"Last error: {str(last_error)}"
        )
        logger.error(error_msg)
        raise AllKeysExhaustedError(error_msg)
    
    @staticmethod
    def _make_request(
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        api_key: str,
        provider: ProviderType,
        timeout: int = 30,
    ) -> Tuple[Any, Dict[str, str]]:
        """
        Make HTTP POST request to provider API.
        
        Returns:
            Tuple of (response_data, response_headers)
            
        Raises:
            RateLimitError: On HTTP 429
            Exception: On other errors
        """
        # Prepare headers
        request_headers = dict(headers)  # Copy to avoid mutation
        request_headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Add authentication
        if provider == ProviderType.GEMINI:
            # Gemini uses API key in URL (handled by caller)
            pass
        elif provider == ProviderType.GROQ:
            request_headers['Authorization'] = f"Bearer {api_key}"
        
        request_headers['Content-Type'] = 'application/json'
        
        # Create and send request
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=request_headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                response_headers = dict(response.headers)
                return response_data, response_headers
        
        except urllib.error.HTTPError as e:
            status_code = e.code
            error_body = e.read().decode('utf-8')
            
            if status_code == 429:
                raise RateLimitError(f"HTTP 429 Rate Limited: {error_body}")
            
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get('error', {}).get('message', error_body)
            except json.JSONDecodeError:
                error_msg = error_body
            
            raise Exception(f"HTTP {status_code}: {error_msg}")
        
        except urllib.error.URLError as e:
            raise Exception(f"URL Error: {str(e)}")
        
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    @staticmethod
    def _parse_rate_limit_headers(
        headers: Dict[str, str],
        provider: ProviderType,
    ) -> Optional[RateLimitInfo]:
        """
        Parse rate-limit information from response headers.
        Different providers use different header names.
        """
        if provider == ProviderType.GROQ:
            # Groq uses: x-ratelimit-remaining-requests, x-ratelimit-remaining-tokens
            remaining_requests = headers.get('x-ratelimit-remaining-requests')
            remaining_tokens = headers.get('x-ratelimit-remaining-tokens')
            limit_requests = headers.get('x-ratelimit-limit-requests')
            limit_tokens = headers.get('x-ratelimit-limit-tokens')
            reset_time = headers.get('x-ratelimit-reset')
            
            if remaining_requests or remaining_tokens:
                return RateLimitInfo(
                    remaining_requests=int(remaining_requests) if remaining_requests else None,
                    remaining_tokens=int(remaining_tokens) if remaining_tokens else None,
                    limit_requests=int(limit_requests) if limit_requests else None,
                    limit_tokens=int(limit_tokens) if limit_tokens else None,
                    reset_time=reset_time,
                )
        
        elif provider == ProviderType.GEMINI:
            # Gemini uses different headers (if any)
            # TODO: Update with actual Gemini rate-limit headers
            pass
        
        return None
    
    @staticmethod
    def _record_call(
        provider: ProviderType,
        key_index: int,
        success: bool,
        error: Optional[str] = None,
        rate_limit_info: Optional[RateLimitInfo] = None,
    ) -> None:
        """Record API call in history for debugging."""
        call_record = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider.value,
            'key_index': key_index,
            'success': success,
            'error': error,
            'rate_limit': {
                'remaining_requests': rate_limit_info.remaining_requests,
                'remaining_tokens': rate_limit_info.remaining_tokens,
            } if rate_limit_info else None,
        }
        APIKeyManager._call_history.append(call_record)
        
        # Keep only recent 1000 calls
        if len(APIKeyManager._call_history) > 1000:
            APIKeyManager._call_history = APIKeyManager._call_history[-1000:]
    
    @staticmethod
    def get_call_history(limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent call history for debugging."""
        return APIKeyManager._call_history[-limit:]
    
    @staticmethod
    def get_provider_stats(provider: ProviderType) -> Dict[str, Any]:
        """Get statistics for a specific provider."""
        if provider not in APIKeyManager._keys:
            return {}
        
        keys = APIKeyManager._keys[provider]
        
        return {
            'provider': provider.value,
            'total_keys': len(keys),
            'keys': [
                {
                    'index': k.index,
                    'use_count': k.use_count,
                    'error_count': k.error_count,
                    'on_cooldown': k.is_on_cooldown(),
                    'cooldown_until': k.cooldown_until.isoformat() if k.cooldown_until else None,
                    'last_used': k.last_used.isoformat() if k.last_used else None,
                    'last_rate_limited': k.last_rate_limited.isoformat() if k.last_rate_limited else None,
                }
                for k in keys
            ],
        }


# Global instance for convenience
_manager_instance: Optional[APIKeyManager] = None


def get_api_manager() -> APIKeyManager:
    """Get or create global API manager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = APIKeyManager()
    return _manager_instance


def reset_api_manager() -> None:
    """Reset the global API manager (useful for testing)."""
    global _manager_instance
    _manager_instance = None
