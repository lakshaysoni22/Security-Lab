import time
from app.totp_service import totp_service
from app.policy_engine import policy_engine
from app.blockchain_classifier import blockchain_classifier

def test_totp_secret_generation():
    enrollment = totp_service.generate_totp_secret()
    assert "secret" in enrollment
    assert "registration_uri" in enrollment
    assert len(enrollment["secret"]) > 10

def test_totp_token_verification_failure():
    # An invalid code should fail verification
    is_valid = totp_service.verify_totp_token("MFRGGZDFMZTWQ2LK", "000000")
    assert is_valid is False

def test_backup_codes_generation():
    codes = totp_service.generate_backup_codes()
    assert len(codes) == 5
    for code in codes:
        assert len(code) == 8

def test_ip_access_security_policy():
    # Safe IP in IN should pass
    assert policy_engine.verify_ip_access("192.168.1.100", "IN") is True
    # Blacklisted IP should fail
    assert policy_engine.verify_ip_access("198.51.100.42", "IN") is False
    # Geo-blocked country should fail
    assert policy_engine.verify_ip_access("192.168.1.100", "KP") is False

def test_brute_force_account_lockout():
    username = "test_investigator"
    policy_engine.reset_failed_logins(username)
    assert policy_engine.is_account_locked(username) is False
    
    # Trigger 5 failed logins
    for _ in range(5):
        policy_engine.record_failed_login(username)
        
    assert policy_engine.is_account_locked(username) is True
    
    # Reset lock
    policy_engine.reset_failed_logins(username)
    assert policy_engine.is_account_locked(username) is False

def test_blockchain_address_classifier():
    # Test EVM
    res_evm = blockchain_classifier.classify_address("0x71c20e241775e5332f143715df332f143789a71b")
    assert res_evm["blockchain"] == "EVM Compatible"
    
    # Test Bitcoin SegWit
    res_btc_seg = blockchain_classifier.classify_address("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh")
    assert res_btc_seg["blockchain"] == "Bitcoin (BTC)"
    assert "SegWit" in res_btc_seg["address_type"]

    # Test Bitcoin Legacy
    res_btc_leg = blockchain_classifier.classify_address("1AGNa15ZQXAZUgFiqJ2i7Z2DPU2J6hW62i")
    assert res_btc_leg["blockchain"] == "Bitcoin (BTC)"
    assert "Legacy" in res_btc_leg["address_type"]

    # Test Solana
    res_sol = blockchain_classifier.classify_address("HN7cE2q4gY6hy9WcH1b7tD5Ji1b2x7T1b")
    assert res_sol["blockchain"] == "Solana"

    # Test Tron
    res_trx = blockchain_classifier.classify_address("TY1b2x7T1b2x7T1b2x7T1b2x7T1b2x7T1b")
    assert res_trx["blockchain"] == "Tron (TRX)"

