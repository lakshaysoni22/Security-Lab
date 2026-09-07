import uuid
import time
from typing import Dict, List, Any

# Local correlated alerts database for SOC queries
CORRELATED_ALERTS = []

class SIEMCorrelationEngine:
    def correlate_event_stream(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scans a chronological list of log events and groups matching alert sequences."""
        correlated = []
        
        # Look for suspicious sequences: e.g. Failed Logins followed by an Evidence Download
        failed_logins = [e for e in events if e.get("event_type") == "auth_fail"]
        downloads = [e for e in events if e.get("event_type") == "evidence_download"]
        
        if len(failed_logins) >= 3 and len(downloads) >= 1:
            correlation_id = f"corr_{uuid.uuid4()}"
            alert = {
                "correlation_id": correlation_id,
                "pattern": "Brute Force Followed by Evidence Exfiltration",
                "risk_score": 90,
                "confidence_score": 95,
                "events_count": len(failed_logins) + len(downloads),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "recommended_action": "Revoke investigator active session immediately."
            }
            correlated.append(alert)
            CORRELATED_ALERTS.append(alert)
            
        # Look for multi-wallet transfers
        transfers = [e for e in events if e.get("event_type") == "large_transfer"]
        if len(transfers) >= 2:
            correlation_id = f"corr_{uuid.uuid4()}"
            alert = {
                "correlation_id": correlation_id,
                "pattern": "Concurrent Multi-Wallet Whale Transfers",
                "risk_score": 75,
                "confidence_score": 80,
                "events_count": len(transfers),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "recommended_action": "Flag target wallets in Watchlist."
            }
            correlated.append(alert)
            CORRELATED_ALERTS.append(alert)
            
        return correlated

    def get_alerts_history(self) -> List[Dict[str, Any]]:
        """Returns the history of SOC correlated alerts."""
        return CORRELATED_ALERTS

siem_correlation = SIEMCorrelationEngine()
