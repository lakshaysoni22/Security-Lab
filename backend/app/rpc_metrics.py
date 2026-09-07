"""
LEATrace RPC Metrics & Circuit Breaker — Production.

Implements a proper three-state circuit breaker (Closed → Open → Half-Open)
with configurable thresholds, reset timers, and request/failure tracking
per provider.

PRODUCTION INVARIANTS:
- Circuit breaker has three states: CLOSED, OPEN, HALF_OPEN.
- Trips after configurable consecutive failures (default: 5).
- Automatically transitions to HALF_OPEN after recovery timeout.
- Records success rate and latency histograms per provider.
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger("leatrace.rpc_metrics")


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation — requests flow through
    OPEN = "open"           # Circuit tripped — requests blocked
    HALF_OPEN = "half_open" # Recovery probe — allow one request to test


class CircuitBreaker:
    """Per-provider circuit breaker with three-state logic."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0

    def is_allowed(self) -> bool:
        """Checks if a request is allowed through the circuit breaker."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker transitioning to HALF_OPEN")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls

        return False

    def record_success(self):
        """Records a successful request."""
        self.success_count += 1
        if self.state == CircuitState.HALF_OPEN:
            # Successful probe — close the circuit
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
            logger.info("Circuit breaker CLOSED after successful recovery probe")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Records a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Failed probe — reopen the circuit
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker OPEN — recovery probe failed")
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker OPEN — {self.failure_count} consecutive failures"
                )

    def get_status(self) -> dict:
        """Returns circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_s": self.recovery_timeout,
        }


class RPCMetricsTracker:
    """
    Enterprise RPC metrics tracking with per-provider circuit breakers,
    request counting, and latency tracking.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.request_counts: Dict[str, int] = {}
        self.failure_counts: Dict[str, int] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.latency_samples: Dict[str, list] = {}
        self._max_samples = 100

    def _get_breaker(self, provider: str) -> CircuitBreaker:
        """Gets or creates a circuit breaker for a provider."""
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker(
                failure_threshold=self.failure_threshold,
                recovery_timeout=self.recovery_timeout,
            )
        return self.circuit_breakers[provider]

    def is_allowed(self, provider: str) -> bool:
        """Checks if a request to this provider is allowed."""
        return self._get_breaker(provider).is_allowed()

    def record_request(self, provider: str):
        """Records a request attempt."""
        self.request_counts[provider] = self.request_counts.get(provider, 0) + 1

    def record_success(self, provider: str, latency_ms: float = 0.0):
        """Records a successful request with optional latency."""
        self._get_breaker(provider).record_success()

        if latency_ms > 0:
            if provider not in self.latency_samples:
                self.latency_samples[provider] = []
            self.latency_samples[provider].append(latency_ms)
            if len(self.latency_samples[provider]) > self._max_samples:
                self.latency_samples[provider] = self.latency_samples[provider][-self._max_samples:]

    def record_failure(self, provider: str):
        """Records a failed request."""
        self.failure_counts[provider] = self.failure_counts.get(provider, 0) + 1
        self._get_breaker(provider).record_failure()

    def reset_failures(self, provider: str):
        """Records a success (resets failure tracking). Legacy API compatibility."""
        self.record_success(provider)

    def is_tripped(self, provider: str) -> bool:
        """Legacy API: checks if the circuit breaker is in OPEN state."""
        breaker = self._get_breaker(provider)
        return breaker.state == CircuitState.OPEN

    def get_avg_latency(self, provider: str) -> float:
        """Returns average latency for a provider."""
        samples = self.latency_samples.get(provider, [])
        if not samples:
            return 0.0
        return round(sum(samples) / len(samples), 2)

    def get_p95_latency(self, provider: str) -> float:
        """Returns P95 latency for a provider."""
        samples = self.latency_samples.get(provider, [])
        if not samples:
            return 0.0
        sorted_samples = sorted(samples)
        idx = int(len(sorted_samples) * 0.95)
        return round(sorted_samples[min(idx, len(sorted_samples) - 1)], 2)

    def get_success_rate(self, provider: str) -> float:
        """Returns success rate as a percentage."""
        total = self.request_counts.get(provider, 0)
        failures = self.failure_counts.get(provider, 0)
        if total == 0:
            return 100.0
        return round(((total - failures) / total) * 100, 2)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Returns comprehensive metrics for all tracked providers."""
        metrics = {}
        all_providers = set(self.request_counts.keys()) | set(self.circuit_breakers.keys())

        for provider in all_providers:
            short_name = provider[:50] + "..." if len(provider) > 50 else provider
            breaker = self._get_breaker(provider)
            metrics[short_name] = {
                "total_requests": self.request_counts.get(provider, 0),
                "total_failures": self.failure_counts.get(provider, 0),
                "success_rate": self.get_success_rate(provider),
                "avg_latency_ms": self.get_avg_latency(provider),
                "p95_latency_ms": self.get_p95_latency(provider),
                "circuit_breaker": breaker.get_status(),
            }

        return metrics


# Singleton
rpc_metrics = RPCMetricsTracker()
