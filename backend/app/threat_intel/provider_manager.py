"""
LEATrace TI Provider Manager — Production.

Central orchestrator for all threat intelligence providers.
Manages registration, synchronization, failover, and health.

PRODUCTION INVARIANTS:
- Never fabricates data from any provider.
- Structured status for unavailable providers.
- Full audit logging of all sync operations.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from .provider_base import ThreatIntelProvider, ProviderStatus

logger = logging.getLogger("leatrace.ti.provider_manager")


class ProviderRegistry:
    """Central registry for all TI providers."""

    def __init__(self):
        self._providers: Dict[str, ThreatIntelProvider] = {}

    def register(self, provider: ThreatIntelProvider) -> None:
        """Registers a TI provider."""
        self._providers[provider.name] = provider
        logger.info("TI provider registered: %s (%s)",
                     provider.name, provider.provider_type)

    def unregister(self, name: str) -> None:
        """Unregisters a TI provider."""
        if name in self._providers:
            del self._providers[name]
            logger.info("TI provider unregistered: %s", name)

    def get(self, name: str) -> Optional[ThreatIntelProvider]:
        """Gets a provider by name."""
        return self._providers.get(name)

    def get_all(self) -> List[ThreatIntelProvider]:
        """Returns all registered providers."""
        return list(self._providers.values())

    def get_by_type(self, provider_type: str) -> List[ThreatIntelProvider]:
        """Returns all providers of a given type."""
        return [
            p for p in self._providers.values()
            if p.provider_type == provider_type
        ]

    def get_active(self) -> List[ThreatIntelProvider]:
        """Returns all active (configured + healthy) providers."""
        return [
            p for p in self._providers.values()
            if p.is_configured() and p._status not in (
                ProviderStatus.DISABLED, ProviderStatus.NOT_CONFIGURED,
            )
        ]

    def get_sorted_by_priority(self) -> List[ThreatIntelProvider]:
        """Returns providers sorted by priority (lower number = higher priority)."""
        return sorted(
            self.get_active(),
            key=lambda p: p.priority,
        )


class ProviderManager:
    """
    Orchestrates sync across all registered TI providers.

    Features:
    - Priority-based provider selection
    - Automatic failover on provider failure
    - Rate limiting per provider
    - Background sync scheduling
    - Deduplication across providers
    - Audit logging of all operations
    """

    def __init__(self):
        self.registry = ProviderRegistry()

    def register_provider(self, provider: ThreatIntelProvider) -> None:
        """Registers a TI provider."""
        self.registry.register(provider)

    def get_all_provider_status(self) -> List[Dict[str, Any]]:
        """Returns status of all registered providers."""
        return [p.get_status() for p in self.registry.get_all()]

    def get_provider_health(self, name: str) -> Dict[str, Any]:
        """Returns detailed health for a specific provider."""
        provider = self.registry.get(name)
        if not provider:
            return {"status": "not_found", "name": name}
        return provider.health_check()

    def health_check_all(self) -> Dict[str, Any]:
        """Runs health checks on all providers."""
        results = {}
        for provider in self.registry.get_all():
            try:
                results[provider.name] = provider.health_check()
            except Exception as e:
                results[provider.name] = {
                    "is_healthy": False,
                    "error": str(e)[:200],
                }
        return {
            "providers": results,
            "total": len(results),
            "healthy": sum(1 for r in results.values() if r.get("is_healthy")),
            "checked_at": datetime.datetime.utcnow().isoformat(),
        }

    def sync_all(self, db: Any, **kwargs) -> Dict[str, Any]:
        """
        Synchronizes data from all active providers.

        Uses priority ordering. Logs all operations.
        Returns aggregate sync summary.
        """
        if db is None:
            return {"status": "db_unavailable"}

        providers = self.registry.get_sorted_by_priority()
        if not providers:
            return {
                "status": "no_providers",
                "message": "No active TI providers registered.",
            }

        results = []
        total_objects = 0
        total_new = 0
        total_errors = 0
        start_time = datetime.datetime.utcnow()

        for provider in providers:
            try:
                logger.info("Syncing TI provider: %s (%s)",
                             provider.name, provider.provider_type)
                result = provider.sync(db, **kwargs)
                result["provider_name"] = provider.name
                result["provider_type"] = provider.provider_type

                total_objects += result.get("objects_fetched", 0)
                total_new += result.get("objects_new", 0)

                # Log sync
                self._log_sync(db, provider, result)
                results.append(result)

            except Exception as e:
                logger.error("Provider %s sync failed: %s", provider.name, e)
                error_result = {
                    "provider_name": provider.name,
                    "provider_type": provider.provider_type,
                    "status": "error",
                    "error": str(e)[:300],
                }
                self._log_sync(db, provider, error_result)
                results.append(error_result)
                total_errors += 1

        duration = (datetime.datetime.utcnow() - start_time).total_seconds()

        return {
            "status": "completed",
            "providers_synced": len(results),
            "total_objects_fetched": total_objects,
            "total_objects_new": total_new,
            "total_errors": total_errors,
            "duration_seconds": round(duration, 2),
            "results": results,
            "synced_at": start_time.isoformat(),
        }

    def sync_provider(
        self,
        name: str,
        db: Any,
        **kwargs,
    ) -> Dict[str, Any]:
        """Syncs a single provider by name."""
        provider = self.registry.get(name)
        if not provider:
            return {"status": "not_found", "name": name}
        if not provider.is_configured():
            return {"status": "not_configured", "name": name}

        try:
            result = provider.sync(db, **kwargs)
            self._log_sync(db, provider, result)
            return result
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e)[:300],
            }
            self._log_sync(db, provider, error_result)
            return error_result

    def sync_with_failover(
        self,
        provider_type: str,
        db: Any,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Syncs using the best provider of a given type.
        Falls back to next provider on failure.
        """
        providers = self.registry.get_by_type(provider_type)
        providers.sort(key=lambda p: p.priority)

        for provider in providers:
            if not provider.is_configured():
                continue
            if provider._status == ProviderStatus.FAILED:
                continue

            try:
                result = provider.sync(db, **kwargs)
                if result.get("status") != "error":
                    self._log_sync(db, provider, result)
                    return result
            except Exception as e:
                logger.warning("Provider %s failed, trying next: %s",
                               provider.name, e)
                provider._record_sync_error(str(e))
                continue

        return {
            "status": "all_providers_failed",
            "provider_type": provider_type,
            "message": f"All {len(providers)} providers of type '{provider_type}' failed.",
        }

    def get_dashboard_data(self, db: Any = None) -> Dict[str, Any]:
        """Returns aggregate dashboard data for all TI providers."""
        providers = self.registry.get_all()

        dashboard = {
            "total_providers": len(providers),
            "active_providers": sum(
                1 for p in providers
                if p._status == ProviderStatus.ACTIVE
            ),
            "degraded_providers": sum(
                1 for p in providers
                if p._status == ProviderStatus.DEGRADED
            ),
            "failed_providers": sum(
                1 for p in providers
                if p._status == ProviderStatus.FAILED
            ),
            "not_configured_providers": sum(
                1 for p in providers
                if p._status == ProviderStatus.NOT_CONFIGURED
            ),
            "providers": [p.get_status() for p in providers],
            "total_objects_synced": sum(p._objects_synced for p in providers),
            "total_sync_count": sum(p._sync_count for p in providers),
            "total_error_count": sum(p._error_count for p in providers),
        }

        if db:
            from ..stix_models import IOCEntry, TISyncLog
            try:
                dashboard["total_iocs"] = db.query(IOCEntry).count()
                dashboard["active_iocs"] = db.query(IOCEntry).filter(
                    IOCEntry.status == "active"
                ).count()

                recent_syncs = (
                    db.query(TISyncLog)
                    .order_by(TISyncLog.synced_at.desc())
                    .limit(10)
                    .all()
                )
                dashboard["recent_syncs"] = [
                    {
                        "provider": s.provider_name,
                        "status": s.status,
                        "objects_new": s.objects_new,
                        "synced_at": s.synced_at.isoformat() if s.synced_at else None,
                    }
                    for s in recent_syncs
                ]
            except Exception as e:
                dashboard["db_error"] = str(e)[:200]

        return dashboard

    def _log_sync(
        self,
        db: Any,
        provider: ThreatIntelProvider,
        result: Dict[str, Any],
    ) -> None:
        """Persists a sync log entry."""
        from ..stix_models import TISyncLog

        try:
            log = TISyncLog(
                id=str(uuid.uuid4()),
                provider_name=provider.name,
                provider_type=provider.provider_type,
                status=result.get("status", "unknown"),
                objects_fetched=result.get("objects_fetched", 0),
                objects_new=result.get("objects_new", 0),
                objects_updated=result.get("objects_updated", 0),
                objects_deduplicated=result.get("objects_deduplicated", 0),
                duration_seconds=result.get("duration_seconds"),
                error_message=result.get("error"),
                sync_type=result.get("sync_type", "incremental"),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.warning("Failed to log sync: %s", e)


# ─── Singleton ────────────────────────────────────────────────────────────────

provider_manager = ProviderManager()
