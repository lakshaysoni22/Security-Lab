import pytest
from app.stix_engine import stix_engine
from app.taxii_client import taxii_client
from app.sigma_engine import sigma_engine
from app.yara_engine import yara_engine
from app.attack_engine import attack_engine
from app.ioc_engine import ioc_engine

def test_stix_object_creation():
    ind = stix_engine.create_indicator("Scam Wallet", "[cryptocurrency-address:value = '0x123']")
    assert ind["type"] == "indicator"
    assert ind["name"] == "Scam Wallet"
    assert ind["spec_version"] == "2.1"
    
    mal = stix_engine.create_malware("Ransomware Tool", "Encrypts local databases")
    assert mal["type"] == "malware"
    
    rel = stix_engine.create_relationship(ind["id"], mal["id"], "indicates")
    assert rel["type"] == "relationship"
    assert rel["relationship_type"] == "indicates"

def test_taxii_client_sync():
    root = taxii_client.get_api_root_information()
    # If TAXII_SERVER_URL is not configured, return early—no server to test against
    if root.get("status") == "not_configured":
        pytest.skip("TAXII_SERVER_URL not configured — skipping live server test")
    assert "versions" in root
    assert "taxii-2.1" in root["versions"]
    
    colls = taxii_client.list_collections()
    if colls and colls[0].get("status") == "not_configured":
        pytest.skip("TAXII not configured")
    assert len(colls) >= 1
    
    objects = taxii_client.sync_collection_objects(colls[0]["id"])
    assert isinstance(objects, list)

def test_sigma_parser_and_evaluator():
    sigma_yaml = """
title: Suspicious Login Attempt
status: experimental
description: Detects logins from forbidden Admin tools
logsource:
    category: authentication
detection:
    selection:
        username: admin
        is_failed: true
    condition: selection
"""
    rule = sigma_engine.parse_rule(sigma_yaml)
    assert rule["title"] == "Suspicious Login Attempt"
    
    # Test match
    log_match = {"username": "admin", "is_failed": True, "ip": "192.168.1.1"}
    assert sigma_engine.evaluate_rule(rule, log_match) is True
    
    # Test mismatch
    log_mismatch = {"username": "user1", "is_failed": True}
    assert sigma_engine.evaluate_rule(rule, log_mismatch) is False

def test_yara_scanner():
    yara_rule = """
rule Ransomware_Alert {
    strings:
        $a = "cryptolocker"
        $b = /ransom[0-9]/
    condition:
        any of them
}
"""
    compiled = yara_engine.compile_rule(yara_rule)
    assert len(compiled["strings"]) == 2
    
    # Scan matches
    matches1 = yara_engine.scan_content(compiled, "File contains cryptolocker process logs")
    assert "a" in matches1
    
    matches2 = yara_engine.scan_content(compiled, "File contains ransom5 alert codes")
    assert "b" in matches2

def test_mitre_attack_tagger():
    # Map phishing
    res_phish = attack_engine.map_log_to_technique("Received phishing attachment in corporate mailbox")
    assert res_phish["mapped"] is True
    assert res_phish["technique_id"] == "T1566"
    assert res_phish["tactic_name"] == "Initial Access"
    
    # Map exfiltration
    res_exfil = attack_engine.map_log_to_technique("S3 bucket data exfiltration leak detected")
    assert res_exfil["mapped"] is True
    assert res_exfil["technique_id"] == "T1048"

def test_ioc_repository_check():
    # Query domain IOC
    res = ioc_engine.check_ioc("blocktrace-forensics-bypass.com")
    assert res["flagged"] is True
    assert res["type"] == "domain"
    
    # Add new hash IOC
    new_ioc = ioc_engine.add_ioc("hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    assert new_ioc["ioc_id"] == "ioc_004"
    assert new_ioc["type"] == "hash"
    
    # Verify addition
    res_added = ioc_engine.check_ioc("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    assert res_added["flagged"] is True
