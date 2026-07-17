"""
Test and demo module for API Key Rotation System.

This module demonstrates:
1. Loading multiple API keys from .env
2. Normal successful API calls
3. Automatic fallback on rate-limiting
4. Cooldown behavior
5. Statistics and debugging
"""

import os
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import urllib.error

from .api_client import (
    APIKeyManager,
    ProviderType,
    RateLimitError,
    AllKeysExhaustedError,
    get_api_manager,
    reset_api_manager,
)

# Set up logging to see debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_load_and_display_keys():
    """
    Demo 1: Load and display all available API keys.
    Shows which keys were loaded from environment.
    """
    logger.info("\n" + "="*80)
    logger.info("DEMO 1: Loading and Displaying API Keys")
    logger.info("="*80)
    
    reset_api_manager()
    manager = get_api_manager()
    
    # Display loaded keys
    for provider in [ProviderType.GEMINI, ProviderType.GROQ]:
        stats = manager.get_provider_stats(provider)
        
        if stats:
            logger.info(f"\n{provider.value.upper()}:")
            logger.info(f"  Total keys: {stats['total_keys']}")
            for key_info in stats['keys']:
                logger.info(
                    f"  Key #{key_info['index']}: "
                    f"uses={key_info['use_count']}, "
                    f"errors={key_info['error_count']}, "
                    f"cooldown={key_info['on_cooldown']}"
                )
        else:
            logger.warning(f"\n{provider.value.upper()}: No keys loaded!")
    
    return manager


def demo_successful_call_with_mocking():
    """
    Demo 2: Simulate a successful API call with proper headers.
    Shows that the first key is used successfully.
    """
    logger.info("\n" + "="*80)
    logger.info("DEMO 2: Successful API Call (Mocked)")
    logger.info("="*80)
    
    reset_api_manager()
    manager = get_api_manager()
    
    # Mock successful response with rate-limit headers
    mock_response_data = {
        "choices": [{
            "message": {
                "content": "This is a successful response from Groq API"
            }
        }]
    }
    
    mock_response_headers = {
        'x-ratelimit-remaining-requests': '99',
        'x-ratelimit-remaining-tokens': '50000',
        'x-ratelimit-limit-requests': '100',
        'x-ratelimit-limit-tokens': '100000',
    }
    
    def mock_urlopen(req, timeout=None):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode('utf-8')
        mock_response.headers = mock_response_headers
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=None)
        return mock_response
    
    with patch('urllib.request.urlopen', side_effect=mock_urlopen):
        try:
            response_data, rate_limit_info, key_index = manager.call_provider(
                provider=ProviderType.GROQ,
                url="https://api.groq.com/openai/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                payload={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": "Hello Groq!"}]
                },
            )
            
            logger.info(f"\n✓ Call succeeded using key #{key_index}")
            logger.info(f"  Response: {response_data.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
            
            if rate_limit_info:
                logger.info(
                    f"  Rate limit: {rate_limit_info.remaining_requests} "
                    f"requests / {rate_limit_info.remaining_tokens} tokens remaining"
                )
            
            # Display updated stats
            stats = manager.get_provider_stats(ProviderType.GROQ)
            logger.info(f"\n  Updated key #{key_index} stats:")
            for key_info in stats['keys']:
                if key_info['index'] == key_index:
                    logger.info(f"    Uses: {key_info['use_count']}, Errors: {key_info['error_count']}")
            
            return True
        
        except Exception as e:
            logger.error(f"\n✗ Call failed: {str(e)}")
            return False


def demo_rate_limit_fallback():
    """
    Demo 3: Simulate hitting rate limit on first key, then falling back to second key.
    This is the main use case for the rotation system.
    """
    logger.info("\n" + "="*80)
    logger.info("DEMO 3: Rate Limit Fallback (First Key → Second Key)")
    logger.info("="*80)
    
    reset_api_manager()
    manager = get_api_manager()
    
    # Get current stats before the test
    logger.info("\nInitial stats:")
    for key_info in manager.get_provider_stats(ProviderType.GROQ)['keys']:
        logger.info(f"  Key #{key_info['index']}: uses={key_info['use_count']}, errors={key_info['error_count']}")
    
    # Mock responses: first key returns 429, second key succeeds
    call_count = [0]  # Use list to allow modification in nested function
    
    def mock_urlopen_with_fallback(req, timeout=None):
        call_count[0] += 1
        
        if call_count[0] == 1:
            # First call: return 429 (rate limit)
            logger.info("\n  [Mock] First call: Returning HTTP 429 Rate Limit")
            error_response = json.dumps({
                "error": {
                    "message": "Rate limit exceeded",
                    "type": "rate_limit_error"
                }
            }).encode('utf-8')
            
            http_error = urllib.error.HTTPError(
                url="https://api.groq.com/openai/v1/chat/completions",
                code=429,
                msg="Too Many Requests",
                hdrs={},
                fp=StringIO(error_response.decode('utf-8'))
            )
            http_error.read = Mock(return_value=error_response)
            raise http_error
        
        else:
            # Second call: succeed with different key
            logger.info("  [Mock] Second call: Returning successful response")
            mock_response_data = {
                "choices": [{
                    "message": {
                        "content": "Success! This is from the fallback key (key #1)"
                    }
                }]
            }
            
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_response_data).encode('utf-8')
            mock_response.headers = {
                'x-ratelimit-remaining-requests': '98',
                'x-ratelimit-remaining-tokens': '49000',
            }
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=None)
            return mock_response
    
    with patch('urllib.request.urlopen', side_effect=mock_urlopen_with_fallback):
        try:
            logger.info("\nMaking API call (will auto-fallback on rate-limit)...")
            
            response_data, rate_limit_info, key_index = manager.call_provider(
                provider=ProviderType.GROQ,
                url="https://api.groq.com/openai/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                payload={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": "Hello with fallback!"}]
                },
                max_retries=3,
            )
            
            logger.info(f"\n✓ Call succeeded using fallback key #{key_index}")
            logger.info(f"  Response: {response_data['choices'][0]['message']['content']}")
            
            # Display updated stats showing the fallback
            logger.info(f"\nFinal stats after fallback:")
            stats = manager.get_provider_stats(ProviderType.GROQ)
            for key_info in stats['keys']:
                status = "⏸ COOLDOWN" if key_info['on_cooldown'] else "✓ READY"
                logger.info(
                    f"  Key #{key_info['index']}: "
                    f"uses={key_info['use_count']}, "
                    f"errors={key_info['error_count']}, "
                    f"status={status}"
                )
            
            return True
        
        except Exception as e:
            logger.error(f"\n✗ Call failed: {str(e)}")
            return False


def demo_all_keys_exhausted():
    """
    Demo 4: Simulate all keys being rate-limited (exhausted scenario).
    Shows AllKeysExhaustedError being raised.
    """
    logger.info("\n" + "="*80)
    logger.info("DEMO 4: All Keys Exhausted (HTTP 429 from all keys)")
    logger.info("="*80)
    
    reset_api_manager()
    manager = get_api_manager()
    
    logger.info(f"\nAvailable keys: {len(manager.get_available_keys(ProviderType.GROQ))}")
    
    # Mock all keys returning 429
    def mock_urlopen_all_fail(req, timeout=None):
        logger.info("  [Mock] Returning HTTP 429")
        error_response = json.dumps({
            "error": {"message": "Rate limit exceeded"}
        }).encode('utf-8')
        
        http_error = urllib.error.HTTPError(
            url="https://api.groq.com/openai/v1/chat/completions",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=StringIO(error_response.decode('utf-8'))
        )
        http_error.read = Mock(return_value=error_response)
        raise http_error
    
    with patch('urllib.request.urlopen', side_effect=mock_urlopen_all_fail):
        try:
            logger.info("\nMaking API call (all keys will be exhausted)...")
            
            response_data, _, _ = manager.call_provider(
                provider=ProviderType.GROQ,
                url="https://api.groq.com/openai/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                payload={"model": "llama-3.1-8b-instant"},
                max_retries=10,  # Will try all available keys
            )
            
            logger.error("\n✗ Should have raised AllKeysExhaustedError!")
            return False
        
        except AllKeysExhaustedError as e:
            logger.info(f"\n✓ AllKeysExhaustedError raised as expected:")
            logger.info(f"  {str(e)}")
            
            # Show all keys are on cooldown
            logger.info(f"\nFinal key states:")
            stats = manager.get_provider_stats(ProviderType.GROQ)
            for key_info in stats['keys']:
                logger.info(
                    f"  Key #{key_info['index']}: "
                    f"on_cooldown={key_info['on_cooldown']}, "
                    f"cooldown_until={key_info['cooldown_until']}"
                )
            
            return True
        
        except Exception as e:
            logger.error(f"\n✗ Unexpected error: {str(e)}")
            return False


def demo_call_history():
    """
    Demo 5: Display call history for debugging.
    Shows which keys were used, success/failure, and timing.
    """
    logger.info("\n" + "="*80)
    logger.info("DEMO 5: Call History for Debugging")
    logger.info("="*80)
    
    manager = get_api_manager()
    
    history = manager.get_call_history(limit=10)
    
    if not history:
        logger.info("\nNo call history available")
        return
    
    logger.info(f"\nRecent {len(history)} calls:")
    for i, call in enumerate(history, 1):
        status = "✓" if call['success'] else "✗"
        logger.info(
            f"  {i}. [{status}] {call['provider'].upper()} key #{call['key_index']} "
            f"at {call['timestamp']}"
        )
        if call['error']:
            logger.info(f"     Error: {call['error']}")
        if call['rate_limit']:
            logger.info(
                f"     Rate limit: {call['rate_limit']['remaining_requests']} "
                f"requests, {call['rate_limit']['remaining_tokens']} tokens"
            )


def run_all_demos():
    """Run all demo functions in sequence."""
    logger.info("\n\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " API Key Rotation System - Complete Demo Suite ".center(78) + "║")
    logger.info("╚" + "="*78 + "╝")
    
    demos = [
        ("Load and Display Keys", demo_load_and_display_keys),
        ("Successful API Call", demo_successful_call_with_mocking),
        ("Rate Limit Fallback", demo_rate_limit_fallback),
        ("All Keys Exhausted", demo_all_keys_exhausted),
        ("Call History", demo_call_history),
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        try:
            result = demo_func()
            results.append((demo_name, True, result))
        except Exception as e:
            logger.exception(f"\n✗ Demo '{demo_name}' failed with exception:")
            results.append((demo_name, False, str(e)))
    
    # Summary
    logger.info("\n\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " Demo Summary ".center(78) + "║")
    logger.info("╚" + "="*78 + "╝")
    
    for demo_name, success, result in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {demo_name}")
    
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    logger.info(f"\nTotal: {passed}/{total} demos completed successfully")


if __name__ == '__main__':
    # Run all demos
    run_all_demos()
