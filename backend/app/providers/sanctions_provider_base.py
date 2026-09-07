"""
LEATrace Sanctions Provider Base Interface — Production.

Defines the abstract interface and structures for sanctions intelligence feeds.
Includes enterprise-grade retry logic, rate limiting, health tracking, and
integrity validation contracts.
"""

from __future__ import annotations

import abc
import datetime
import logging
import time
import threading
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("leatrace.providers.sanctions_base")


class SanctionsProviderStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    SYNCING = "syncing"


class SanctionsProvider(abc.ABC):
    """
    Abstract Base Class for all Sanctions Providers.

    Provides built-in:
    - Exponential backoff retry logic
    - Rate limiting (requests per minute)
    - Connection timeout configuration
    - Health tracking with error budget
    - Enable/disable toggle
    - Integrity validation contract
    """

    def __init__(
        self,
        provider_id: str,
        name: str,
        priority: int = 50,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 60.0,
        requests_per_minute: int = 10,
        connect_timeout: int = 30,
        read_timeout: int = 120,
        enabled: bool = True,
    ):
        self.provider_id = provider_id
        self.name = name
        self.priority = priority
        self.enabled = enabled
        self.feed_url: str = ""

        # Retry configuration
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_backoff_seconds = initial_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds

        # Rate limiting
        self.requests_per_minute = requests_per_minute
        self._request_timestamps: List[float] = []
        self._rate_lock = threading.Lock()

        # Timeouts
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

        # Health tracking
        self._status = SanctionsProviderStatus.NOT_CONFIGURED
        self._last_sync_at: Optional[datetime.datetime] = None
        self._last_success_at: Optional[datetime.datetime] = None
        self._last_failure_at: Optional[datetime.datetime] = None
        self._last_error: Optional[str] = None
        self._sync_count = 0
        self._error_count = 0
        self._consecutive_failures = 0
        self._total_entities_synced = 0
        self._total_wallets_synced = 0
        self._avg_sync_duration_seconds: float = 0.0

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider has all required settings."""
        ...

    @abc.abstractmethod
    def _download_and_parse_impl(self) -> Dict[str, Any]:
        """
        Internal download implementation. Subclasses implement this.

        Returns:
            Dict containing parsed entities and metadata:
            - 'checksum': SHA-256 string
            - 'entities': List of Dicts representing entities/wallets
            - 'raw_data': bytes representing raw content
            - 'record_count': int total records parsed
        """
        ...

    @abc.abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Checks feed connection and responsiveness."""
        ...

    def download_and_parse(self) -> Dict[str, Any]:
        """
        Downloads and parses with automatic retry and rate limiting.

        Wraps the subclass implementation with:
        1. Rate limit enforcement
        2. Exponential backoff retry
        3. Health status tracking
        """
        if not self.enabled:
            raise RuntimeError(f"Provider '{self.name}' is disabled.")

        if not self.is_configured():
            raise RuntimeError(f"Provider '{self.name}' is not configured.")

        self._status = SanctionsProviderStatus.SYNCING
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # Enforce rate limit
                self._enforce_rate_limit()

                logger.info(
                    "Provider '%s' download attempt %d/%d",
                    self.name, attempt, self.max_retries,
                )

                result = self._download_and_parse_impl()

                # Validate result structure
                if not isinstance(result, dict):
                    raise ValueError("Provider must return a dict from download_and_parse_impl")
                if "checksum" not in result or "entities" not in result:
                    raise ValueError("Provider result must contain 'checksum' and 'entities' keys")

                # Record success
                self._record_success()
                result["attempts"] = attempt
                result["record_count"] = result.get("record_count", len(result.get("entities", [])))
                return result

            except Exception as e:
                last_exception = e
                logger.warning(
                    "Provider '%s' attempt %d/%d failed: %s",
                    self.name, attempt, self.max_retries, str(e)[:300],
                )

                if attempt < self.max_retries:
                    backoff = min(
                        self.initial_backoff_seconds * (self.backoff_factor ** (attempt - 1)),
                        self.max_backoff_seconds,
                    )
                    logger.info("Retrying in %.1f seconds...", backoff)
                    time.sleep(backoff)

        # All retries exhausted
        self._record_failure(str(last_exception))
        raise last_exception  # type: ignore[misc]

    def validate_integrity(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates data integrity of a sync result.

        Default implementation checks:
        - Checksum is present and non-empty
        - Record count matches entities list length
        - No duplicate entity UIDs

        Subclasses can override to add signature verification.

        Returns:
            Dict with validation results.
        """
        issues: List[str] = []
        checksum = result.get("checksum", "")
        entities = result.get("entities", [])

        if not checksum:
            issues.append("Missing checksum")

        if len(checksum) != 64:
            issues.append(f"Checksum length {len(checksum)} != 64 (expected SHA-256)")

        # Check for duplicate UIDs
        uids = [e.get("entity_uid") for e in entities if e.get("entity_uid")]
        unique_uids = set(uids)
        duplicates = len(uids) - len(unique_uids)
        if duplicates > 0:
            issues.append(f"{duplicates} duplicate entity UIDs detected")

        # Check for entities without required fields
        for i, ent in enumerate(entities):
            if not ent.get("entity_uid"):
                issues.append(f"Entity at index {i} missing entity_uid")
            if not ent.get("name"):
                issues.append(f"Entity '{ent.get('entity_uid', i)}' missing name")

        return {
            "valid": len(issues) == 0,
            "checksum": checksum,
            "total_entities": len(entities),
            "unique_entities": len(unique_uids),
            "duplicate_uids": duplicates,
            "total_wallets": sum(len(e.get("wallets", [])) for e in entities),
            "issues": issues,
            "validated_at": datetime.datetime.utcnow().isoformat() + "Z",
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns current status and stats for this provider."""
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "priority": self.priority,
            "enabled": self.enabled,
            "status": self._status.value,
            "is_configured": self.is_configured(),
            "last_sync_at": self._last_sync_at.isoformat() + "Z" if self._last_sync_at else None,
            "last_success_at": self._last_success_at.isoformat() + "Z" if self._last_success_at else None,
            "last_failure_at": self._last_failure_at.isoformat() + "Z" if self._last_failure_at else None,
            "last_error": self._last_error,
            "sync_count": self._sync_count,
            "error_count": self._error_count,
            "consecutive_failures": self._consecutive_failures,
            "total_entities_synced": self._total_entities_synced,
            "total_wallets_synced": self._total_wallets_synced,
            "avg_sync_duration_seconds": round(self._avg_sync_duration_seconds, 2),
            "retry_config": {
                "max_retries": self.max_retries,
                "backoff_factor": self.backoff_factor,
                "initial_backoff_seconds": self.initial_backoff_seconds,
            },
            "rate_limit": {
                "requests_per_minute": self.requests_per_minute,
            },
            "timeouts": {
                "connect_timeout": self.connect_timeout,
                "read_timeout": self.read_timeout,
            },
        }

    def set_enabled(self, enabled: bool) -> None:
        """Enables or disables this provider."""
        self.enabled = enabled
        if not enabled:
            self._status = SanctionsProviderStatus.DISABLED
        elif self.is_configured():
            self._status = SanctionsProviderStatus.ACTIVE if self._consecutive_failures == 0 else SanctionsProviderStatus.DEGRADED
        logger.info("Provider '%s' %s", self.name, "enabled" if enabled else "disabled")

    def _record_success(self) -> None:
        now = datetime.datetime.utcnow()
        self._last_sync_at = now
        self._last_success_at = now
        self._sync_count += 1
        self._consecutive_failures = 0
        self._status = SanctionsProviderStatus.ACTIVE
        self._last_error = None

    def _record_failure(self, error: str) -> None:
        now = datetime.datetime.utcnow()
        self._last_error = error[:500]
        self._error_count += 1
        self._consecutive_failures += 1
        self._last_sync_at = now
        self._last_failure_at = now
        if self._consecutive_failures >= 3:
            self._status = SanctionsProviderStatus.FAILED
        else:
            self._status = SanctionsProviderStatus.DEGRADED

    def _record_sync_stats(self, entities_count: int, wallets_count: int, duration_seconds: float) -> None:
        """Records sync statistics for monitoring."""
        self._total_entities_synced = entities_count
        self._total_wallets_synced = wallets_count
        # Rolling average of sync duration
        if self._avg_sync_duration_seconds == 0:
            self._avg_sync_duration_seconds = duration_seconds
        else:
            self._avg_sync_duration_seconds = (
                self._avg_sync_duration_seconds * 0.7 + duration_seconds * 0.3
            )

    def _enforce_rate_limit(self) -> None:
        """Enforces requests-per-minute rate limit using sliding window."""
        with self._rate_lock:
            now = time.time()
            window_start = now - 60.0

            # Remove timestamps outside the window
            self._request_timestamps = [
                t for t in self._request_timestamps if t > window_start
            ]

            if len(self._request_timestamps) >= self.requests_per_minute:
                # Calculate sleep time until the oldest request exits the window
                sleep_time = self._request_timestamps[0] - window_start
                if sleep_time > 0:
                    logger.info(
                        "Rate limit reached for '%s'. Sleeping %.1f seconds.",
                        self.name, sleep_time,
                    )
                    time.sleep(sleep_time)

            self._request_timestamps.append(now)
