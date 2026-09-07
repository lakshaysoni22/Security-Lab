"""
LEATrace MITRE ATT&CK TI Provider — Production.

Integrates the MITRE ATT&CK STIX 2.1 dataset from the official
public repository. Replaces the hardcoded 4-technique attack_engine.

PRODUCTION INVARIANTS:
- Downloads real MITRE ATT&CK STIX data from the official GitHub repo.
- Never fabricates techniques or threat groups.
- If download fails → returns structured error status.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
from typing import Any, Dict

from ..provider_base import ThreatIntelProvider

logger = logging.getLogger("leatrace.ti.providers.mitre_attack")

# Official MITRE ATT&CK STIX 2.1 data URL
MITRE_ATTACK_ENTERPRISE_URL = os.getenv(
    "MITRE_ATTACK_URL",
    "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
)


class MITREAttackProvider(ThreatIntelProvider):
    """
    MITRE ATT&CK STIX 2.1 provider.

    Downloads the full Enterprise ATT&CK matrix from the official
    MITRE CTI GitHub repository and ingests all STIX objects
    (Attack Patterns, Intrusion Sets, Malware, Tools, etc.) into
    the local database.

    This replaces the hardcoded attack_engine.py that only had
    4 keyword-matched techniques.
    """

    def __init__(
        self,
        name: str = "mitre_attack",
        priority: int = 20,
    ):
        super().__init__(name=name, provider_type="mitre_attack", priority=priority)
        self._url = MITRE_ATTACK_ENTERPRISE_URL

    def is_configured(self) -> bool:
        """MITRE ATT&CK is always available (public dataset)."""
        return bool(self._url)

    def sync(self, db: Any, **kwargs) -> Dict[str, Any]:
        """
        Downloads and ingests the MITRE ATT&CK STIX bundle.

        This is a full sync — the entire dataset is downloaded each time.
        Objects are upserted (existing objects updated, new ones created).
        """
        import httpx

        if not self.is_configured():
            return {
                "status": "not_configured",
                "message": "MITRE ATT&CK URL not configured.",
            }

        start = datetime.datetime.utcnow()
        objects_fetched = 0
        objects_new = 0
        objects_updated = 0
        errors = 0

        try:
            logger.info("Downloading MITRE ATT&CK STIX bundle from %s", self._url)

            response = httpx.get(
                self._url,
                timeout=120.0,
                follow_redirects=True,
            )
            response.raise_for_status()

            bundle = response.json()
            if not isinstance(bundle, dict) or bundle.get("type") != "bundle":
                return {
                    "status": "error",
                    "error": "Downloaded data is not a valid STIX bundle.",
                }

            from ...stix_engine import stix_engine

            stix_objects = bundle.get("objects", [])
            logger.info("MITRE ATT&CK bundle contains %d objects", len(stix_objects))

            for obj in stix_objects:
                if not isinstance(obj, dict):
                    continue
                objects_fetched += 1

                try:
                    stix_engine.validate_object(obj)
                    row_id = stix_engine.ingest_object_to_db(
                        obj, db,
                        source_provider=self.name,
                    )
                    if row_id:
                        objects_new += 1
                except Exception as ve:
                    errors += 1
                    if errors <= 5:
                        logger.debug("MITRE STIX validation error: %s", ve)

            db.commit()
            duration = (datetime.datetime.utcnow() - start).total_seconds()
            self._record_sync_success(objects_fetched, objects_new)

            logger.info(
                "MITRE ATT&CK sync complete: fetched=%d new=%d errors=%d duration=%.1fs",
                objects_fetched, objects_new, errors, duration,
            )

            return {
                "status": "success",
                "objects_fetched": objects_fetched,
                "objects_new": objects_new,
                "objects_updated": objects_updated,
                "errors": errors,
                "duration_seconds": round(duration, 2),
                "sync_type": "full",
                "source_url": self._url,
            }

        except httpx.HTTPError as e:
            self._record_sync_error(str(e))
            return {
                "status": "error",
                "error": f"HTTP error downloading MITRE ATT&CK data: {e}",
            }
        except Exception as e:
            self._record_sync_error(str(e))
            return {
                "status": "error",
                "error": str(e)[:300],
            }

    def health_check(self) -> Dict[str, Any]:
        """Checks connectivity to the MITRE ATT&CK data source."""
        import httpx

        try:
            resp = httpx.head(self._url, timeout=10.0, follow_redirects=True)
            return {
                "is_healthy": resp.status_code == 200,
                "status_code": resp.status_code,
                "url": self._url,
                "latency_ms": resp.elapsed.total_seconds() * 1000 if resp.elapsed else None,
            }
        except Exception as e:
            return {
                "is_healthy": False,
                "error": str(e)[:200],
                "url": self._url,
            }

    def lookup_technique(self, technique_id: str, db: Any) -> Dict[str, Any]:
        """
        Looks up a MITRE ATT&CK technique by ID (e.g., T1059).

        Returns the technique from the local STIX DB — never fabricated.
        """
        from ...stix_models import StixAttackPattern

        if db is None:
            return {"status": "db_unavailable"}

        try:
            # Search external_references for the technique ID
            patterns = (
                db.query(StixAttackPattern)
                .filter(StixAttackPattern.source_provider == self.name)
                .all()
            )

            for pattern in patterns:
                ext_refs = pattern.external_references or []
                for ref in ext_refs:
                    if isinstance(ref, dict) and ref.get("external_id") == technique_id.upper():
                        return {
                            "status": "found",
                            "technique_id": technique_id.upper(),
                            "stix_id": pattern.stix_id,
                            "name": pattern.name,
                            "description": pattern.description,
                            "kill_chain_phases": pattern.kill_chain_phases,
                            "external_references": pattern.external_references,
                            "source": "mitre_attack_local_db",
                        }

            return {
                "status": "not_found",
                "technique_id": technique_id,
                "message": "Technique not in local DB. Run POST /api/ti/sync to populate.",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}

    def list_techniques(self, db: Any, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Lists all MITRE ATT&CK techniques from the local DB."""
        from ...stix_models import StixAttackPattern

        if db is None:
            return {"status": "db_unavailable"}

        try:
            query = (
                db.query(StixAttackPattern)
                .filter(StixAttackPattern.source_provider == self.name)
            )
            total = query.count()
            items = query.order_by(StixAttackPattern.name).offset(skip).limit(limit).all()

            return {
                "total": total,
                "skip": skip,
                "limit": limit,
                "techniques": [
                    {
                        "stix_id": p.stix_id,
                        "name": p.name,
                        "description": (p.description or "")[:200],
                        "kill_chain_phases": p.kill_chain_phases,
                        "external_references": p.external_references,
                    }
                    for p in items
                ],
                "data_source": "mitre_attack_local_db",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}
