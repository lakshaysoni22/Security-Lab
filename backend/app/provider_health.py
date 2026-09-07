"""
LEATrace Blockchain Intelligence — Provider Health Monitor.

Production health monitoring with history tracking, degradation alerting,
sustained failure detection, and auto-disable for tripped providers.
Uses httpx connection pool for health pings.
"""

import time
import json
import logging
from typing import Dict, Any, List
from collections import deque

logger = logging.getLogger("leatrace.provider_health")


class ProviderHealthMonitor:
    """Enterprise RPC provider health monitoring with history and alerting."""

    def __init__(self):
        self.health_history: Dict[str, Any] = {}
        self._ping_history: Dict[str, deque] = {}  # Last 100 pings per provider
        self._failure_counts: Dict[str, int] = {}
        self._auto_disabled: Dict[str, float] = {}  # Provider -> disable_until timestamp
        self._max_history = 100
        self._auto_disable_threshold = 5  # consecutive failures to auto-disable
        self._auto_disable_duration = 60.0  # seconds to keep disabled

    def ping_provider(self, url: str) -> Dict[str, Any]:
        """Pings an RPC provider and records health metrics."""
        # Check if auto-disabled
        if url in self._auto_disabled:
            if time.time() < self._auto_disabled[url]:
                return {
                    "is_healthy": False,
                    "latency_ms": 0.0,
                    "rate_limited": False,
                    "error_message": "auto_disabled",
                    "auto_disabled_until": self._auto_disabled[url],
                }
            else:
                del self._auto_disabled[url]
                self._failure_counts[url] = 0

        # Use httpx connection pool for health pings
        from .connection_pool import connection_pool

        payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
        start = time.time()

        try:
            response = connection_pool.post_json(url, payload, timeout=4)
            latency = (time.time() - start) * 1000

            if response is None:
                raise ConnectionError("No response from provider")

            is_healthy = "result" in response

            status = {
                "is_healthy": is_healthy,
                "latency_ms": round(latency, 1),
                "rate_limited": False,
                "error_message": None,
                "timestamp": time.time(),
            }
            self._record_ping(url, status)
            self._failure_counts[url] = 0
            return status
        except Exception as e:
            error_str = str(e)
            is_rate_limited = "429" in error_str
            status = {
                "is_healthy": False,
                "latency_ms": 0.0,
                "rate_limited": is_rate_limited,
                "error_message": error_str[:200],
                "timestamp": time.time(),
            }
            self._record_ping(url, status)

            # Track consecutive failures
            self._failure_counts[url] = self._failure_counts.get(url, 0) + 1
            if self._failure_counts[url] >= self._auto_disable_threshold:
                self._auto_disabled[url] = time.time() + self._auto_disable_duration
                logger.warning(f"Provider auto-disabled for {self._auto_disable_duration}s: {url[:50]}")

            return status

    def _record_ping(self, url: str, status: Dict[str, Any]):
        """Records a ping result in history."""
        self.health_history[url] = status
        if url not in self._ping_history:
            self._ping_history[url] = deque(maxlen=self._max_history)
        self._ping_history[url].append(status)

    def get_provider_history(self, url: str) -> List[Dict[str, Any]]:
        """Returns ping history for a provider."""
        return list(self._ping_history.get(url, []))

    def get_uptime_percentage(self, url: str) -> float:
        """Calculates uptime percentage from ping history."""
        history = self._ping_history.get(url, [])
        if not history:
            return 0.0
        healthy_count = sum(1 for p in history if p.get("is_healthy", False))
        return round((healthy_count / len(history)) * 100, 1)

    def get_avg_latency(self, url: str) -> float:
        """Returns average latency from ping history."""
        history = self._ping_history.get(url, [])
        latencies = [p["latency_ms"] for p in history if p.get("is_healthy") and p.get("latency_ms", 0) > 0]
        if not latencies:
            return 0.0
        return round(sum(latencies) / len(latencies), 1)

    def is_auto_disabled(self, url: str) -> bool:
        """Checks if a provider is auto-disabled."""
        if url in self._auto_disabled:
            if time.time() < self._auto_disabled[url]:
                return True
            del self._auto_disabled[url]
        return False

    def get_all_health_status(self) -> Dict[str, Any]:
        """Returns comprehensive health status for all monitored providers."""
        result = {}
        for url, status in self.health_history.items():
            result[url[:50]] = {
                "healthy": status.get("is_healthy", False),
                "latency_ms": status.get("latency_ms", 0),
                "uptime_pct": self.get_uptime_percentage(url),
                "avg_latency_ms": self.get_avg_latency(url),
                "auto_disabled": self.is_auto_disabled(url),
                "consecutive_failures": self._failure_counts.get(url, 0),
                "history_size": len(self._ping_history.get(url, [])),
            }
        return result


health_monitor = ProviderHealthMonitor()
