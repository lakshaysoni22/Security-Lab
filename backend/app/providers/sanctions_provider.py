"""
LEATrace Sanctions Provider Facade — Production.

Provides a backward-compatible facade to the DB-backed Sanctions Screening Engine.
This replaces the legacy in-memory OFAC parser and guarantees that all screening
calls project onto the consolidated database dataset.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..database import SessionLocal
from ..sanctions_models import SanctionsListWallet, SanctionsListEntity, SanctionsVersionHistory
from ..sanctions_screening_engine import sanctions_screening_engine

logger = logging.getLogger("leatrace.providers.facade")


class SanctionsProviderFacade:
    """Facade for the sanctions screening engine to match the legacy ofac_provider interface."""

    def is_sanctioned(self, address: str) -> bool:
        """Checks if a crypto wallet address is on any active sanctions list."""
        if not address:
            return False
        db = SessionLocal()
        try:
            res = sanctions_screening_engine.screen_wallet(address, db=db, checked_by="facade")
            return res.get("sanctioned", False)
        except Exception as e:
            logger.error("Facade is_sanctioned failed: %s", e)
            return False
        finally:
            db.close()

    def get_sanction_details(self, address: str) -> Optional[Dict[str, Any]]:
        """Returns details of a sanctioned wallet address from the database."""
        if not address:
            return None
        db = SessionLocal()
        try:
            res = sanctions_screening_engine.screen_wallet(address, db=db, checked_by="facade")
            if res.get("sanctioned"):
                entity = res.get("matched_entity")
                if entity:
                    # Map to the format expected by the frontend / legacy callers
                    return {
                        "entity": entity["name"],
                        "uid": entity["entity_uid"],
                        "list": entity["provider_id"].upper(),
                        "programs": entity["program"].split(";") if entity["program"] else [],
                        "type": entity["entity_type"].capitalize(),
                        "risk": "Critical",
                        "currency": entity.get("currency", "Cryptocurrency"),
                    }
            return None
        except Exception as e:
            logger.error("Facade get_sanction_details failed: %s", e)
            return None
        finally:
            db.close()

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Searches sanctions entries by name (fuzzy matching)."""
        if not query:
            return []
        db = SessionLocal()
        try:
            # If query looks like an address, screen as address
            if len(query) >= 26 and (query.startswith("0x") or query.startswith("1") or query.startswith("3") or query.startswith("bc1")):
                res = sanctions_screening_engine.screen_wallet(query, db=db, checked_by="facade")
                if res.get("sanctioned") and res.get("matched_entity"):
                    ent = res["matched_entity"]
                    return [{
                        "address": query,
                        "entity": ent["name"],
                        "uid": ent["entity_uid"],
                        "list": ent["provider_id"].upper(),
                        "programs": ent["program"].split(";") if ent["program"] else [],
                        "type": ent["entity_type"].capitalize(),
                        "risk": "Critical",
                        "currency": ent.get("currency", "Cryptocurrency"),
                    }]
                return []

            # Otherwise screen as entity name
            res = sanctions_screening_engine.screen_entity_name(query, db=db, min_confidence=0.7, checked_by="facade")
            legacy_results = []
            for match in res.get("matches", []):
                for wallet in match.get("wallets", []):
                    legacy_results.append({
                        "address": wallet["address"],
                        "entity": match["name"],
                        "uid": match["entity_uid"],
                        "list": match["provider_id"].upper(),
                        "programs": match["program"].split(";") if match["program"] else [],
                        "type": match["entity_type"].capitalize(),
                        "risk": "Critical",
                        "currency": wallet["currency"],
                    })
            return legacy_results
        except Exception as e:
            logger.error("Facade search failed: %s", e)
            return []
        finally:
            db.close()

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics of the active database entries."""
        db = SessionLocal()
        try:
            total_addresses = db.query(SanctionsListWallet).filter(SanctionsListWallet.status == "active").count()
            total_entities = db.query(SanctionsListEntity).filter(SanctionsListEntity.status == "active").count()
            last_version = (
                db.query(SanctionsVersionHistory)
                .filter(SanctionsVersionHistory.status == "success")
                .order_by(SanctionsVersionHistory.synced_at.desc())
                .first()
            )
            return {
                "loaded": total_entities > 0,
                "total_addresses": total_addresses,
                "total_entities": total_entities,
                "last_sync": last_version.synced_at.isoformat() if last_version else None,
                "source": "Consolidated Database (OFAC/EU)",
            }
        except Exception as e:
            logger.error("Facade get_stats failed: %s", e)
            return {
                "loaded": False,
                "total_addresses": 0,
                "total_entities": 0,
                "error": str(e),
            }
        finally:
            db.close()


# Singleton Facade
ofac_provider = SanctionsProviderFacade()
