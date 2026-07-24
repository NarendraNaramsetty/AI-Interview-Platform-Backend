import os
import time
import threading
import logging
from django.utils import timezone
from .metrics import MetricsCollector

logger = logging.getLogger(__name__)

# Configurable via environment variables
AI_BREAKER_FAILURE_THRESHOLD = int(os.getenv("AI_BREAKER_FAILURE_THRESHOLD", 5))
AI_BREAKER_WINDOW_SECONDS = int(os.getenv("AI_BREAKER_WINDOW_SECONDS", 120))
AI_BREAKER_COOLDOWN_SECONDS = int(os.getenv("AI_BREAKER_COOLDOWN_SECONDS", 60))

class CircuitBreaker:
    _lock = threading.Lock()
    _instances = {}

    def __new__(cls, provider: str = "default"):
        with cls._lock:
            if provider not in cls._instances:
                instance = super(CircuitBreaker, cls).__new__(cls)
                instance.provider = provider
                instance.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
                instance.failures = []
                instance.cooldown_until = 0.0
                cls._instances[provider] = instance
            return cls._instances[provider]

    @classmethod
    def reset_all(cls):
        """Helper to clear state across unit tests."""
        with cls._lock:
            cls._instances.clear()

    def allow_request(self) -> bool:
        """
        Checks if the request is allowed.
        If the state is OPEN and cooldown has expired, transitions to HALF-OPEN to allow trial.
        """
        now = time.time()
        with self._lock:
            if self.state == "OPEN":
                if now >= self.cooldown_until:
                    self.state = "HALF-OPEN"
                    logger.info(f"Circuit breaker for provider '{self.provider}' transitioned to HALF-OPEN.")
                    MetricsCollector.set_gauge("circuit_breaker_state", 0.5, {"provider": self.provider})
                    return True
                else:
                    return False
            return True

    def record_success(self):
        """Resets failures and closes the breaker upon a successful trial request."""
        with self._lock:
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failures = []
                logger.info(f"Circuit breaker for provider '{self.provider}' reset to CLOSED.")
                MetricsCollector.set_gauge("circuit_breaker_state", 0, {"provider": self.provider})

    def record_failure(self):
        """Records a failure and trips the breaker if threshold is reached."""
        now = time.time()
        with self._lock:
            self.failures.append(now)
            # Remove failures outside of the rolling window
            cutoff = now - AI_BREAKER_WINDOW_SECONDS
            self.failures = [t for t in self.failures if t >= cutoff]

            if self.state == "HALF-OPEN" or len(self.failures) >= AI_BREAKER_FAILURE_THRESHOLD:
                self.state = "OPEN"
                self.cooldown_until = now + AI_BREAKER_COOLDOWN_SECONDS
                logger.warning(
                    f"Circuit breaker for provider '{self.provider}' tripped to OPEN. "
                    f"Cooldown active until {self.cooldown_until}. Total failures in window: {len(self.failures)}"
                )
                MetricsCollector.increment_counter("circuit_breaker_trip_total", {"provider": self.provider})
                MetricsCollector.set_gauge("circuit_breaker_state", 1, {"provider": self.provider})
