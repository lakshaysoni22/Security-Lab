import time
from typing import Dict, List, Any

class AttackChainEngine:
    def reconstruct_incident_chain(self, correlation_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Arranges correlated logs into a reconstructed timeline mapped to MITRE attack phases."""
        timeline = []
        
        # Sort logs chronologically
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", 0))
        
        for idx, event in enumerate(sorted_events):
            event_type = event.get("event_type")
            phase = "Discovery"
            tech_id = "T1082"
            
            if event_type == "auth_fail":
                phase = "Initial Access"
                tech_id = "T1110" # Brute Force
            elif event_type == "evidence_download":
                phase = "Exfiltration"
                tech_id = "T1048" # Exfil alternative protocol
            elif event_type == "large_transfer":
                phase = "Impact"
                tech_id = "T1496" # Resource Hijacking
                
            timeline.append({
                "step": idx + 1,
                "timestamp": event.get("timestamp", int(time.time())),
                "event_type": event_type,
                "mitre_phase": phase,
                "technique_id": tech_id,
                "description": event.get("description", "Event processed in attack chain")
            })
            
        return {
            "correlation_id": correlation_id,
            "reconstructed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "steps_count": len(timeline),
            "timeline": timeline
        }

attack_chain = AttackChainEngine()
