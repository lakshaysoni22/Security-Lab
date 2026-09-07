"""
LEATrace Threat Intelligence Database — Production.

Queries sanctions entries from the database rather than a hardcoded dict.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .sanctions_screening_engine import sanctions_screening_engine
from . import models

logger = logging.getLogger("leatrace.threat_database")


class ThreatIntelligenceDatabase:
    """
    DB-backed threat intelligence lookup.

    Methods:
      check_sanction(address, db)  — Check if an address is sanctioned
      list_sanctions(db, limit)    — List all sanctions entries (paginated)
      check_stix_indicator(address, db) — Check against STIX indicators
    """

    def check_sanction(self, address: str, db: Any = None) -> Optional[Dict[str, Any]]:
        """
        Checks if a crypto address appears in the sanctions_list_wallets table
        or the legacy sanctions_entries table.

        Args:
            address: Crypto wallet address to check
            db:      SQLAlchemy session. If None, logs a warning and returns None.

        Returns:
            Dict with sanction details if found, None otherwise.
            Never fabricates data.
        """
        if not address:
            return None

        if db is None:
            logger.warning(
                "check_sanction called without DB session — cannot query. "
                "Pass a SQLAlchemy session to perform live sanctions lookup."
            )
            return None

        try:
            # 1. Screen wallet address using the new unified screening engine
            res = sanctions_screening_engine.screen_wallet(
                address=address,
                db=db,
                checked_by="threat_db",
                reason_context="Unified threat database query",
            )
            
            if res.get("sanctioned") and res.get("matched_entity"):
                ent = res["matched_entity"]
                return {
                    "address":     address,
                    "owner":       ent["name"],
                    "registry":    ent["provider_id"].upper(),
                    "program":     ent["program"],
                    "source_id":   ent["entity_uid"],
                    "entry_type":  ent["entity_type"],
                    "severity":    "Critical",
                    "data_source": "database",
                }

            # 2. Fallback to legacy table if the new tables are empty
            addr_lower = address.strip().lower()
            entry = (
                db.query(models.SanctionsEntry)
                .filter(models.SanctionsEntry.address == addr_lower)
                .first()
            )
            if entry:
                return {
                    "address":     entry.address,
                    "owner":       entry.entity_name,
                    "registry":    entry.list_type,
                    "program":     entry.program,
                    "source_id":   entry.source_id,
                    "entry_type":  entry.entry_type,
                    "severity":    "Critical",
                    "data_source": "database_legacy",
                }
            return None

        except Exception as e:
            logger.error("Sanctions DB lookup failed for %s: %s", address, e)
            return None

    def check_stix_indicator(self, address: str, db: Any = None) -> Optional[Dict[str, Any]]:
        """
        Checks if a crypto address appears in STIX indicators (from TAXII sync).

        Args:
            address: Crypto wallet address
            db:      SQLAlchemy session

        Returns:
            STIX indicator context if found, None otherwise.
        """
        if not address or db is None:
            return None

        try:
            # Search pattern field for the address
            indicators = (
                db.query(models.StixIndicator)
                .filter(models.StixIndicator.pattern.contains(address))
                .all()
            )
            if not indicators:
                return None

            first = indicators[0]
            return {
                "matched": True,
                "stix_id": first.stix_id,
                "name": first.name,
                "pattern": first.pattern,
                "collection_id": first.collection_id,
                "confidence": first.confidence,
                "data_source": "stix_indicator_db",
            }
        except Exception as e:
            logger.error("STIX indicator lookup failed for %s: %s", address, e)
            return None

    def list_sanctions(
        self,
        db: Any,
        skip: int = 0,
        limit: int = 50,
        list_type: Optional[str] = None,
        address_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Returns paginated list of sanctions entries from DB.

        Args:
            db:           SQLAlchemy session (required)
            skip:         Pagination offset
            limit:        Page size (max 500)
            list_type:    Filter by "OFAC_SDN" or "EU_CONSOLIDATED"
            address_only: If True, only return entries with a crypto address

        Returns:
            Dict with total count + entries list.
        """
        if db is None:
            return {"status": "error", "message": "DB session required"}

        try:
            # Use the new normalized model if available
            from .sanctions_models import SanctionsListEntity, SanctionsListWallet
            
            # Check if new normalized table is populated
            if db.query(SanctionsListWallet).count() > 0:
                query = db.query(SanctionsListWallet).join(SanctionsListEntity)
                if list_type:
                    query = query.filter(SanctionsListEntity.provider_id == list_type.lower())
                
                total = query.count()
                items = query.offset(skip).limit(min(limit, 500)).all()

                return {
                    "total": total,
                    "skip": skip,
                    "limit": limit,
                    "entries": [
                        {
                            "id":          e.id,
                            "address":     e.address,
                            "entity_name": e.entity.name,
                            "program":     e.entity.program,
                            "list_type":   e.entity.provider_id.upper(),
                            "entry_type":  e.entity.entity_type,
                            "source_id":   e.entity.entity_uid,
                        }
                        for e in items
                    ],
                    "data_source": "database_normalized",
                }

            # Otherwise, fallback to the legacy model
            query = db.query(models.SanctionsEntry)
            if list_type:
                query = query.filter(models.SanctionsEntry.list_type == list_type)
            if address_only:
                query = query.filter(models.SanctionsEntry.address.isnot(None))

            total = query.count()
            items = query.offset(skip).limit(min(limit, 500)).all()

            return {
                "total": total,
                "skip": skip,
                "limit": limit,
                "entries": [
                    {
                        "id":          e.id,
                        "address":     e.address,
                        "entity_name": e.entity_name,
                        "program":     e.program,
                        "list_type":   e.list_type,
                        "entry_type":  e.entry_type,
                        "source_id":   e.source_id,
                    }
                    for e in items
                ],
                "data_source": "database_legacy",
            }
        except Exception as e:
            logger.error("Sanctions list failed: %s", e)
            return {"status": "error", "message": str(e)}


# ─── Singleton ────────────────────────────────────────────────────────────────

threat_db = ThreatIntelligenceDatabase()
