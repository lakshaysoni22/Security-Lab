"""
LEATrace Wallet Enrichment Engine — Production.

DB-backed wallet enrichment that queries real sanctions and STIX tables.
Replaces the previous implementation that used the hardcoded SANCTION_FEEDS dict.

PRODUCTION INVARIANTS:
- Queries only from DB — never fabricates enrichment data.
- If DB is unavailable, returns a clear "unavailable" status.
- If address not found in any source, returns "not_listed" with data source info.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .threat_database import threat_db

logger = logging.getLogger("leatrace.wallet_enrichment")


class WalletEnrichmentEngine:
    """
    Production wallet enrichment using DB-backed sanctions and STIX lookups.

    Checks:
    1. sanctions_entries table (OFAC SDN, EU Consolidated)
    2. stix_indicators table (TAXII synced indicators)
    """

    def enrich_wallet(self, address: str, db: Optional[Any] = None) -> Dict[str, Any]:
        """
        Enriches a wallet address with threat intelligence from DB.

        Args:
            address: Crypto wallet address to look up
            db:      SQLAlchemy session. Required for DB lookups.
                     If None, returns "db_unavailable" status.

        Returns:
            Enrichment dict with is_listed, source, risk tier.
            Never fabricates data.
        """
        if not address:
            return {
                "address": address,
                "is_listed": False,
                "owner": None,
                "source_feed": None,
                "risk_tier": None,
                "status": "invalid_address",
            }

        if db is None:
            logger.warning(
                "enrich_wallet called without DB session for address %s. "
                "Pass a DB session to enable sanctions lookup.",
                address[:12],
            )
            return {
                "address":     address,
                "is_listed":   False,
                "owner":       None,
                "source_feed": None,
                "risk_tier":   None,
                "status":      "db_unavailable",
                "notice":      "Pass a database session to enable real sanctions lookup.",
            }

        # 1. Sanctions DB check
        sanction = threat_db.check_sanction(address, db=db)
        if sanction:
            return {
                "address":     address,
                "is_listed":   True,
                "owner":       sanction.get("owner"),
                "source_feed": sanction.get("registry"),
                "program":     sanction.get("program"),
                "risk_tier":   sanction.get("severity", "Critical"),
                "source_id":   sanction.get("source_id"),
                "data_source": "sanctions_db",
                "status":      "listed",
            }

        # 2. STIX indicator check
        stix_hit = threat_db.check_stix_indicator(address, db=db)
        if stix_hit:
            return {
                "address":     address,
                "is_listed":   True,
                "owner":       stix_hit.get("name"),
                "source_feed": f"STIX:{stix_hit.get('collection_id', 'unknown')}",
                "risk_tier":   "High",
                "stix_id":     stix_hit.get("stix_id"),
                "confidence":  stix_hit.get("confidence"),
                "data_source": "stix_indicator_db",
                "status":      "listed",
            }

        return {
            "address":     address,
            "is_listed":   False,
            "owner":       None,
            "source_feed": None,
            "risk_tier":   None,
            "data_source": "database",
            "status":      "not_listed",
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

wallet_enricher = WalletEnrichmentEngine()
