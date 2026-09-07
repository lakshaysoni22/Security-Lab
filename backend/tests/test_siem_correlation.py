import pytest
from app.correlation_engine import siem_correlation
from app.attack_chain_engine import attack_chain

def test_siem_failed_logins_and_download_correlation():
    events = [
        {"event_type": "auth_fail", "timestamp": 100, "description": "Failed login"},
        {"event_type": "auth_fail", "timestamp": 110, "description": "Failed login"},
        {"event_type": "auth_fail", "timestamp": 120, "description": "Failed login"},
        {"event_type": "evidence_download", "timestamp": 150, "description": "Downloaded secret file"}
    ]
    
    alerts = siem_correlation.correlate_event_stream(events)
    assert len(alerts) == 1
    assert alerts[0]["pattern"] == "Brute Force Followed by Evidence Exfiltration"
    assert alerts[0]["risk_score"] == 90
    assert alerts[0]["confidence_score"] == 95

def test_siem_large_transfers_correlation():
    events = [
        {"event_type": "large_transfer", "timestamp": 200, "description": "Transferred 10 BTC"},
        {"event_type": "large_transfer", "timestamp": 210, "description": "Transferred 20 BTC"}
    ]
    
    alerts = siem_correlation.correlate_event_stream(events)
    assert len(alerts) == 1
    assert alerts[0]["pattern"] == "Concurrent Multi-Wallet Whale Transfers"
    assert alerts[0]["risk_score"] == 75

def test_attack_chain_timeline_reconstruction():
    events = [
        {"event_type": "auth_fail", "timestamp": 100, "description": "Failed login brute force"},
        {"event_type": "evidence_download", "timestamp": 150, "description": "Exfiltrated case data"},
        {"event_type": "large_transfer", "timestamp": 200, "description": "Transferred locked tokens"}
    ]
    
    chain = attack_chain.reconstruct_incident_chain("corr_abc", events)
    assert chain["correlation_id"] == "corr_abc"
    assert chain["steps_count"] == 3
    
    timeline = chain["timeline"]
    assert timeline[0]["event_type"] == "auth_fail"
    assert timeline[0]["mitre_phase"] == "Initial Access"
    assert timeline[0]["technique_id"] == "T1110"
    
    assert timeline[1]["event_type"] == "evidence_download"
    assert timeline[1]["mitre_phase"] == "Exfiltration"
    assert timeline[1]["technique_id"] == "T1048"

    assert timeline[2]["event_type"] == "large_transfer"
    assert timeline[2]["mitre_phase"] == "Impact"
