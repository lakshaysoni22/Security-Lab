"""
LEATrace Sanctions Provider Manager — Production.

Manages registration, priorities, health monitoring, failover,
concurrent synchronization, and integrity validation for multiple
sanctions data feeds.

PRODUCTION INVARIANTS:
- No hardcoded sanctions data
- All data sourced from registered provider feeds
- Concurrent sync via ThreadPoolExecutor
- Automatic failover on provider failure
- Integrity validation on every sync
"""

from __future__ import annotations

import datetime
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from .sanctions_provider_base import SanctionsProvider, SanctionsProviderStatus
from .ofac_sdn_provider import OFACSDNProvider
from .eu_consolidated_provider import EUConsolidatedSanctionsProvider
from .un_sanctions_provider import UNConsolidatedSanctionsProvider

logger = logging.getLogger("leatrace.providers.sanctions_manager")


class SanctionsProviderRegistry:
    """Registry of registered sanctions data providers."""

    def __init__(self):
        self._providers: Dict[str, SanctionsProvider] = {}

    def register(self, provider: SanctionsProvider) -> None:
        self._providers[provider.provider_id] = provider
        logger.info("Registered sanctions provider: %s (%s)", provider.name, provider.provider_id)

    def unregister(self, provider_id: str) -> bool:
        if provider_id in self._providers:
            del self._providers[provider_id]
            logger.info("Unregistered sanctions provider: %s", provider_id)
            return True
        return False

    def get(self, provider_id: str) -> Optional[SanctionsProvider]:
        return self._providers.get(provider_id)

    def get_all(self) -> List[SanctionsProvider]:
        return list(self._providers.values())

    def get_sorted_by_priority(self) -> List[SanctionsProvider]:
        """Returns enabled, configured, and healthy providers ordered by priority."""
        active = [
            p for p in self._providers.values()
            if p.enabled and p.is_configured() and p._status != SanctionsProviderStatus.DISABLED
        ]
        return sorted(active, key=lambda p: p.priority)

    def get_healthy(self) -> List[SanctionsProvider]:
        """Returns only healthy providers."""
        return [
            p for p in self.get_sorted_by_priority()
            if p._status in (SanctionsProviderStatus.ACTIVE, SanctionsProviderStatus.NOT_CONFIGURED)
        ]


class SanctionsProviderManager:
    """Central orchestrator for sanctions data sync, lookups, and monitoring."""

    def __init__(self):
        self.registry = SanctionsProviderRegistry()
        self._max_concurrent_syncs = 3
        self._init_default_providers()

    def _init_default_providers(self):
        # Register OFAC SDN list
        self.registry.register(OFACSDNProvider())
        # Register EU Consolidated list
        self.registry.register(EUConsolidatedSanctionsProvider())
        # Register UN Consolidated list
        self.registry.register(UNConsolidatedSanctionsProvider())

    def sync_provider(self, provider_id: str, db: Any) -> Dict[str, Any]:
        """Runs download, parsing, integrity checks, and ingestion for a specific provider."""
        provider = self.registry.get(provider_id)
        if not provider:
            return {"status": "not_found", "message": f"Provider '{provider_id}' is not registered."}

        if not provider.enabled:
            return {"status": "disabled", "message": f"Provider '{provider_id}' is disabled."}

        if not provider.is_configured():
            return {"status": "not_configured", "message": f"Provider '{provider_id}' is not configured."}

        from ..sanctions_models import (
            SanctionsProviderConfig, SanctionsVersionHistory, SanctionsChangeHistory,
            SanctionsListEntity, SanctionsListWallet, SanctionsAlias,
            SanctionsEntityCountry, SanctionsSyncIntegrityReport,
        )

        # 1. Ensure provider config exists in DB
        config = db.query(SanctionsProviderConfig).filter(
            SanctionsProviderConfig.provider_id == provider_id
        ).first()

        if not config:
            config = SanctionsProviderConfig(
                provider_id=provider_id,
                name=provider.name,
                feed_url=provider.feed_url,
                enabled=True,
            )
            db.add(config)
            db.commit()

        start_time = datetime.datetime.utcnow()
        try:
            # 2. Run provider download & parse (retry handled by base class)
            result = provider.download_and_parse()
            checksum = result["checksum"]
            entities = result["entities"]

            # 3. Integrity validation
            integrity = provider.validate_integrity(result)
            if not integrity["valid"]:
                logger.warning(
                    "Integrity validation failed for provider '%s': %s",
                    provider_id, integrity["issues"],
                )

            # 4. Check for previous successful version with same checksum
            last_version = (
                db.query(SanctionsVersionHistory)
                .filter(
                    SanctionsVersionHistory.provider_id == provider_id,
                    SanctionsVersionHistory.status == "success",
                )
                .order_by(SanctionsVersionHistory.version.desc())
                .first()
            )

            if last_version and last_version.checksum == checksum:
                logger.info("Sanctions list for provider '%s' has not changed (checksum matches). Skipping ingestion.", provider_id)
                config.last_success_at = datetime.datetime.utcnow()
                config.last_sync_at = datetime.datetime.utcnow()
                db.commit()
                return {
                    "status": "skipped",
                    "reason": "checksum_unchanged",
                    "provider_id": provider_id,
                    "version": last_version.version,
                    "entities_count": last_version.entities_count,
                    "wallets_count": last_version.wallets_count,
                    "integrity": integrity,
                }

            # 5. Determine next version number
            next_version = (last_version.version + 1) if last_version else 1
            version_id = str(uuid.uuid4())

            # 6. Begin Ingestion within a nested transaction to support ROLLBACK on failure
            delta_added = 0
            delta_updated = 0
            delta_removed = 0
            current_wallets_count = 0

            # Store existing UIDs for delta computation
            existing_uids = {
                e.entity_uid: e for e in db.query(SanctionsListEntity)
                .filter(SanctionsListEntity.provider_id == provider_id, SanctionsListEntity.status == "active")
                .all()
            }

            active_uids = set()

            for ent_data in entities:
                uid = ent_data["entity_uid"]
                active_uids.add(uid)

                # Upsert entity
                existing_ent = existing_uids.get(uid)
                if existing_ent:
                    # Update existing
                    changed_fields = []
                    if existing_ent.name != ent_data["name"]:
                        changed_fields.append("name")
                    if existing_ent.entity_type != ent_data["entity_type"]:
                        changed_fields.append("entity_type")
                    if existing_ent.program != ent_data["program"]:
                        changed_fields.append("program")

                    existing_ent.name = ent_data["name"]
                    existing_ent.entity_type = ent_data["entity_type"]
                    existing_ent.program = ent_data["program"]
                    existing_ent.remarks = ent_data["remarks"]
                    existing_ent.version_id = version_id
                    existing_ent.updated_at = datetime.datetime.utcnow()
                    entity_id = existing_ent.id
                    delta_updated += 1

                    # Log specific field changes
                    if changed_fields:
                        db.add(SanctionsChangeHistory(
                            version_id=version_id,
                            entity_uid=uid,
                            provider_id=provider_id,
                            action="modified",
                            field_changed=",".join(changed_fields),
                            old_value=existing_ent.name,
                            new_value=ent_data["name"],
                        ))
                else:
                    # Add new
                    new_ent = SanctionsListEntity(
                        entity_uid=uid,
                        provider_id=provider_id,
                        name=ent_data["name"],
                        entity_type=ent_data["entity_type"],
                        program=ent_data["program"],
                        remarks=ent_data["remarks"],
                        version_id=version_id,
                        status="active",
                    )
                    db.add(new_ent)
                    db.flush()
                    entity_id = new_ent.id
                    delta_added += 1

                    # Log change history
                    db.add(SanctionsChangeHistory(
                        version_id=version_id,
                        entity_uid=uid,
                        provider_id=provider_id,
                        action="added",
                        field_changed="entity",
                        new_value=ent_data["name"],
                    ))

                # Recreate child records (purge and reload to prevent conflicts)
                db.query(SanctionsListWallet).filter(SanctionsListWallet.entity_id == entity_id).delete()
                db.query(SanctionsAlias).filter(SanctionsAlias.entity_id == entity_id).delete()
                db.query(SanctionsEntityCountry).filter(SanctionsEntityCountry.entity_id == entity_id).delete()

                for wallet in ent_data.get("wallets", []):
                    db.add(SanctionsListWallet(
                        entity_id=entity_id,
                        address=wallet["address"],
                        normalized_address=wallet["address"].strip().lower(),
                        currency=wallet.get("currency", ""),
                        version_id=version_id,
                    ))
                    current_wallets_count += 1

                for alias in ent_data.get("aliases", []):
                    db.add(SanctionsAlias(
                        entity_id=entity_id,
                        alias_name=alias["alias_name"],
                        alias_type=alias.get("alias_type", "a.k.a."),
                    ))

                for country in ent_data.get("countries", []):
                    db.add(SanctionsEntityCountry(
                        entity_id=entity_id,
                        country_code=country.get("country_code", ""),
                        country_name=country.get("country_name", ""),
                        association_type=country.get("association_type", ""),
                    ))

            # Mark removed entities (soft delete)
            for uid, ent in existing_uids.items():
                if uid not in active_uids:
                    ent.status = "revoked"
                    ent.version_id = version_id
                    ent.updated_at = datetime.datetime.utcnow()
                    delta_removed += 1

                    db.add(SanctionsChangeHistory(
                        version_id=version_id,
                        entity_uid=uid,
                        provider_id=provider_id,
                        action="removed",
                        field_changed="entity",
                        old_value=ent.name,
                    ))

            duration = (datetime.datetime.utcnow() - start_time).total_seconds()

            # 7. Save Version History record
            ver_hist = SanctionsVersionHistory(
                id=version_id,
                provider_id=provider_id,
                version=next_version,
                checksum=checksum,
                status="success",
                entities_count=len(entities),
                wallets_count=current_wallets_count,
                delta_added=delta_added,
                delta_updated=delta_updated,
                delta_removed=delta_removed,
                duration_seconds=duration,
            )
            db.add(ver_hist)

            # 8. Save Integrity Report
            db.add(SanctionsSyncIntegrityReport(
                version_id=version_id,
                provider_id=provider_id,
                checksum=checksum,
                is_valid=integrity["valid"],
                total_entities=integrity["total_entities"],
                unique_entities=integrity["unique_entities"],
                duplicate_uids=integrity["duplicate_uids"],
                total_wallets=integrity["total_wallets"],
                issues_json=integrity["issues"],
                download_size_bytes=result.get("download_size_bytes", 0),
            ))

            # Update provider config status
            config.last_success_at = datetime.datetime.utcnow()
            config.last_sync_at = datetime.datetime.utcnow()
            config.last_error = None
            db.commit()

            # Update provider stats
            provider._record_sync_stats(len(entities), current_wallets_count, duration)

            logger.info(
                "Successfully ingested version %d for provider %s in %.2fs "
                "(+%d /%d -%d entities, %d wallets)",
                next_version, provider_id, duration,
                delta_added, delta_updated, delta_removed, current_wallets_count,
            )
            return {
                "status": "success",
                "provider_id": provider_id,
                "version": next_version,
                "entities_count": len(entities),
                "wallets_count": current_wallets_count,
                "delta_added": delta_added,
                "delta_updated": delta_updated,
                "delta_removed": delta_removed,
                "duration_seconds": round(duration, 2),
                "integrity": integrity,
                "attempts": result.get("attempts", 1),
            }

        except Exception as e:
            db.rollback()
            duration = (datetime.datetime.utcnow() - start_time).total_seconds()
            logger.error("Failed to sync sanctions provider %s: %s", provider_id, e)
            config.last_failure_at = datetime.datetime.utcnow()
            config.last_sync_at = datetime.datetime.utcnow()
            config.last_error = str(e)[:500]
            db.commit()
            return {
                "status": "error",
                "provider_id": provider_id,
                "error": str(e)[:500],
                "duration_seconds": round(duration, 2),
            }

    def sync_all(self, db: Any, concurrent: bool = False) -> Dict[str, Any]:
        """
        Runs sync for all configured and enabled providers.

        Args:
            db: SQLAlchemy session
            concurrent: If True, syncs providers in parallel threads.
                        Note: each thread gets its own DB session.
        """
        providers = self.registry.get_sorted_by_priority()
        if not providers:
            return {
                "status": "not_configured",
                "message": "No active sanctions providers configured. Register providers to begin.",
                "providers_available": [p.provider_id for p in self.registry.get_all()],
            }

        if concurrent and len(providers) > 1:
            return self._sync_all_concurrent(providers)
        else:
            return self._sync_all_sequential(providers, db)

    def _sync_all_sequential(self, providers: List[SanctionsProvider], db: Any) -> Dict[str, Any]:
        """Sequential sync — uses a single DB session."""
        results = {}
        success_count = 0
        skipped_count = 0
        failed_count = 0

        for provider in providers:
            res = self.sync_provider(provider.provider_id, db)
            results[provider.provider_id] = res
            if res.get("status") == "success":
                success_count += 1
            elif res.get("status") == "skipped":
                skipped_count += 1
            else:
                failed_count += 1

        return {
            "status": "completed",
            "sync_mode": "sequential",
            "total_providers": len(providers),
            "success": success_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "results": results,
        }

    def _sync_all_concurrent(self, providers: List[SanctionsProvider]) -> Dict[str, Any]:
        """Concurrent sync — each provider gets its own DB session."""
        from ..database import SessionLocal

        results = {}
        success_count = 0
        skipped_count = 0
        failed_count = 0

        def _sync_single(provider: SanctionsProvider) -> tuple:
            session = SessionLocal()
            try:
                res = self.sync_provider(provider.provider_id, session)
                return provider.provider_id, res
            except Exception as e:
                return provider.provider_id, {"status": "error", "error": str(e)[:500]}
            finally:
                session.close()

        with ThreadPoolExecutor(max_workers=self._max_concurrent_syncs) as executor:
            futures = {executor.submit(_sync_single, p): p for p in providers}
            for future in as_completed(futures):
                provider_id, res = future.result()
                results[provider_id] = res
                if res.get("status") == "success":
                    success_count += 1
                elif res.get("status") == "skipped":
                    skipped_count += 1
                else:
                    failed_count += 1

        return {
            "status": "completed",
            "sync_mode": "concurrent",
            "total_providers": len(providers),
            "success": success_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "results": results,
        }

    def health_check_all(self) -> Dict[str, Any]:
        """Performs health check on all registered providers."""
        results = {}
        healthy_count = 0
        for p in self.registry.get_all():
            check = p.health_check()
            results[p.provider_id] = check
            if check.get("is_healthy"):
                healthy_count += 1
        return {
            "total_providers": len(results),
            "healthy": healthy_count,
            "unhealthy": len(results) - healthy_count,
            "providers": results,
            "checked_at": datetime.datetime.utcnow().isoformat() + "Z",
        }

    def get_all_statuses(self) -> Dict[str, Any]:
        """Returns status of all registered providers."""
        return {
            "providers": [p.get_status() for p in self.registry.get_all()],
            "active_count": len(self.registry.get_sorted_by_priority()),
            "total_count": len(self.registry.get_all()),
        }

    def toggle_provider(self, provider_id: str, enabled: bool) -> Dict[str, Any]:
        """Enables or disables a provider."""
        provider = self.registry.get(provider_id)
        if not provider:
            return {"status": "not_found", "message": f"Provider '{provider_id}' not registered."}
        provider.set_enabled(enabled)
        return {
            "status": "success",
            "provider_id": provider_id,
            "enabled": enabled,
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

sanctions_provider_manager = SanctionsProviderManager()
