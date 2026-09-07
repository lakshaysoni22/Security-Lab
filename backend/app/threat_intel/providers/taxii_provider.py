"""
LEATrace TAXII TI Provider — Production.

Wraps the existing TAXIIClient as a ThreatIntelProvider for the
multi-provider architecture.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict

from ..provider_base import ThreatIntelProvider, ProviderStatus

logger = logging.getLogger("leatrace.ti.providers.taxii")


class TAXIIProvider(ThreatIntelProvider):
    """TAXII 2.1 threat intelligence provider."""

    def __init__(
        self,
        name: str = "taxii_default",
        server_url: str = "",
        priority: int = 40,
    ):
        super().__init__(name=name, provider_type="taxii", priority=priority)
        self._server_url = server_url

    def is_configured(self) -> bool:
        from ...taxii_client import taxii_client
        return taxii_client.is_configured() or bool(self._server_url)

    def sync(self, db: Any, **kwargs) -> Dict[str, Any]:
        """Syncs STIX objects from all TAXII collections."""
        from ...taxii_client import taxii_client
        from ...stix_engine import stix_engine

        if not self.is_configured():
            return {
                "status": "not_configured",
                "message": "TAXII server not configured.",
            }

        start = datetime.datetime.utcnow()
        objects_fetched = 0
        objects_new = 0
        objects_updated = 0
        errors = 0

        try:
            collections = taxii_client.list_collections()
            if not collections or (isinstance(collections[0], dict) and
                                    collections[0].get("status") in ("not_configured", "error")):
                return {
                    "status": "not_configured",
                    "message": "No TAXII collections available.",
                }

            for collection in collections:
                if not isinstance(collection, dict) or "id" not in collection:
                    continue

                coll_id = collection["id"]
                added_after = kwargs.get("added_after")

                try:
                    objects = taxii_client.sync_collection_objects(
                        collection_id=coll_id,
                        added_after=added_after,
                    )

                    for obj in objects:
                        if isinstance(obj, dict) and obj.get("status") in ("not_configured", "error"):
                            continue
                        objects_fetched += 1

                        try:
                            stix_engine.validate_object(obj)
                            row_id = stix_engine.ingest_object_to_db(
                                obj, db,
                                collection_id=coll_id,
                                source_provider=self.name,
                            )
                            if row_id:
                                objects_new += 1
                        except Exception as ve:
                            errors += 1
                            logger.debug("STIX validation error: %s", ve)

                except Exception as e:
                    errors += 1
                    logger.warning("TAXII collection %s sync error: %s", coll_id, e)

            db.commit()
            duration = (datetime.datetime.utcnow() - start).total_seconds()
            self._record_sync_success(objects_fetched, objects_new)

            return {
                "status": "success",
                "objects_fetched": objects_fetched,
                "objects_new": objects_new,
                "objects_updated": objects_updated,
                "errors": errors,
                "collections_synced": len(collections),
                "duration_seconds": round(duration, 2),
                "sync_type": "incremental" if kwargs.get("added_after") else "full",
            }

        except Exception as e:
            self._record_sync_error(str(e))
            return {"status": "error", "error": str(e)[:300]}

    def health_check(self) -> Dict[str, Any]:
        from ...taxii_client import taxii_client
        return taxii_client.health_check()
