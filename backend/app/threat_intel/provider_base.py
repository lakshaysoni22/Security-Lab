"""
LEATrace TI Provider Base — Production.

Abstract base class for all threat intelligence providers.
"""

from __future__ import annotations

import abc
import datetime
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("leatrace.ti.provider_base")


class ProviderStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"


class ThreatIntelProvider(abc.ABC):
    """
    Abstract base for all threat intelligence providers.

    Every TI source (TAXII server, sanctions feed, MITRE ATT&CK, etc.)
    implements this interface for uniform management.
    """

    def __init__(
        self,
        name: str,
        provider_type: str,
        priority: int = 50,
    ):
        self.name = name
        self.provider_type = provider_type
        self.priority = priority
        self._status = ProviderStatus.NOT_CONFIGURED
        self._last_sync: Optional[datetime.datetime] = None
        self._last_error: Optional[str] = None
        self._sync_count: int = 0
        self._error_count: int = 0
        self._objects_synced: int = 0

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider has all required configuration."""
        ...

    @abc.abstractmethod
    def sync(self, db: Any, **kwargs) -> Dict[str, Any]:
        """
        Synchronizes data from the provider.

        Returns:
            Dict with sync results: objects_fetched, objects_new, etc.
            Must never fabricate data.
        """
        ...

    @abc.abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Checks provider connectivity and health.

        Returns:
            Dict with is_healthy, latency_ms, error_message.
        """
        ...

    def get_status(self) -> Dict[str, Any]:
        """Returns current provider status."""
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "status": self._status.value,
            "priority": self.priority,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "last_error": self._last_error,
            "sync_count": self._sync_count,
            "error_count": self._error_count,
            "objects_synced": self._objects_synced,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Returns provider performance metrics."""
        return {
            "name": self.name,
            "type": self.provider_type,
            "sync_count": self._sync_count,
            "error_count": self._error_count,
            "error_rate": (
                round(self._error_count / max(1, self._sync_count) * 100, 1)
            ),
            "objects_synced": self._objects_synced,
        }

    def _record_sync_success(
        self, objects_fetched: int = 0, objects_new: int = 0,
    ) -> None:
        """Records a successful sync."""
        self._last_sync = datetime.datetime.utcnow()
        self._sync_count += 1
        self._objects_synced += objects_new
        self._status = ProviderStatus.ACTIVE

    def _record_sync_error(self, error: str) -> None:
        """Records a sync error."""
        self._last_error = error
        self._error_count += 1
        # Mark as degraded after errors
        if self._error_count >= 3:
            self._status = ProviderStatus.FAILED
        else:
            self._status = ProviderStatus.DEGRADED
