from typing import Dict, Any, List

# Standard MITRE Enterprise tactics
MITRE_TACTICS = {
    "TA0001": "Initial Access",
    "TA0002": "Execution",
    "TA0008": "Lateral Movement",
    "TA0010": "Exfiltration",
    "TA0040": "Impact"
}

# Techniques map
MITRE_TECHNIQUES = {
    "T1566": {"name": "Phishing", "tactic": "TA0001"},
    "T1204": {"name": "User Execution", "tactic": "TA0002"},
    "T1048": {"name": "Exfiltration Over Alternative Protocol", "tactic": "TA0010"},
    "T1485": {"name": "Data Destruction", "tactic": "TA0040"}
}

class ATTACKEngine:
    def map_log_to_technique(self, event_description: str) -> Dict[str, Any]:
        """Automatically parses log keywords and maps them to MITRE Techniques."""
        desc = event_description.lower()
        
        if "phish" in desc or "email link" in desc:
            tech_id = "T1566"
        elif "run file" in desc or "clicked attachment" in desc:
            tech_id = "T1204"
        elif "leak" in desc or "upload to s3" in desc or "exfil" in desc:
            tech_id = "T1048"
        elif "delete db" in desc or "ransom" in desc or "wipe" in desc:
            tech_id = "T1485"
        else:
            return {"mapped": False, "technique_id": None, "technique_name": None, "tactic_name": None}
            
        tech = MITRE_TECHNIQUES[tech_id]
        tactic_name = MITRE_TACTICS[tech["tactic"]]
        
        return {
            "mapped": True,
            "technique_id": tech_id,
            "technique_name": tech["name"],
            "tactic_id": tech["tactic"],
            "tactic_name": tactic_name
        }

attack_engine = ATTACKEngine()
