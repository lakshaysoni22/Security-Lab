from typing import Dict, Any
from .feed_scheduler import feed_scheduler
from .threat_database import threat_db
from .wallet_enrichment import wallet_enricher

class ThreatFeedManager:
    def verify_address_threat(self, address: str) -> Dict[str, Any]:
        enrichment = wallet_enricher.enrich_wallet(address)
        return {
            "query_address": address,
            "threat_detected": enrichment["is_listed"],
            "severity": enrichment["risk_tier"],
            "details": enrichment,
            "last_database_sync": feed_scheduler.last_sync_time
        }

threat_feed_manager = ThreatFeedManager()
