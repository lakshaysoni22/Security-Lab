"""
LEATrace Sanctions TI Provider — Production.

Wraps the existing feed_scheduler as a ThreatIntelProvider.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict

from ..provider_base import ThreatIntelProvider

logger = logging.getLogger("leatrace.ti.providers.sanctions")


class SanctionsProvider(ThreatIntelProvider):
    """Sanctions feed provider (OFAC SDN, EU Consolidated)."""

    def __init__(
        self,
        name: str = "sanctions_default",
        priority: int = 30,
    ):
        super().__init__(name=name, provider_type="sanctions", priority=priority)

    def is_configured(self) -> bool:
        from ...feed_scheduler import feed_scheduler
        return feed_scheduler.is_configured()

    def sync(self, db: Any, **kwargs) -> Dict[str, Any]:
        from ...feed_scheduler import feed_scheduler

        if not self.is_configured():
            return {
                "status": "not_configured",
                "message": "No sanctions sources configured. Set SANCTIONS_SOURCES env var.",
            }

        start = datetime.datetime.utcnow()
        try:
            result = feed_scheduler.run_daily_sync(db=db)
            duration = (datetime.datetime.utcnow() - start).total_seconds()

            objects_new = result.get("total_entries_added", 0)
            self._record_sync_success(
                objects_fetched=objects_new + result.get("total_entries_updated", 0),
                objects_new=objects_new,
            )

            result["duration_seconds"] = round(duration, 2)
            result["objects_fetched"] = objects_new + result.get("total_entries_updated", 0)
            result["objects_new"] = objects_new
            return result

        except Exception as e:
            self._record_sync_error(str(e))
            return {"status": "error", "error": str(e)[:300]}

    def health_check(self) -> Dict[str, Any]:
        from ...feed_scheduler import feed_scheduler
        return {
            "is_healthy": self.is_configured(),
            "configured": self.is_configured(),
            "status": "active" if self.is_configured() else "not_configured",
        }
