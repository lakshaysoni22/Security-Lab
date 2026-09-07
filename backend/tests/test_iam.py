import pytest
from app.oauth_server import oauth_server
from app.oidc_provider import oidc_provider
from app.refresh_service import refresh_service
from app.device_manager import device_manager
from app.session_manager import session_manager
from app.rbac_engine import rbac_engine
from app.abac_engine import abac_engine

def test_oauth_pkce_validation():
    import base64, hashlib, secrets as _secrets
    from unittest.mock import MagicMock

    # Build a lightweight mock DB that captures add() and commit() calls
    mock_db = MagicMock()
    captured_code_obj = {}

    def mock_add(obj):
        captured_code_obj.update({
            "code":                 obj.code,
            "client_id":            obj.client_id,
            "code_challenge":       obj.code_challenge,
            "code_challenge_method": obj.code_challenge_method,
            "expires_at":           obj.expires_at,
            "used":                 obj.used,
        })
    mock_db.add.side_effect = mock_add

    # Generate auth code with PKCE challenge
    challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    code = oauth_server.generate_auth_code(
        client_id="LEAtTrace-frontend",
        user_id="user_101",
        code_challenge=challenge,
        code_challenge_method="S256",
        db=mock_db,
    )
    assert isinstance(code, str)
    assert len(code) > 10

    # Validation with incorrect code should fail (not found)
    mock_db2 = MagicMock()
    mock_db2.query.return_value.filter.return_value.first.return_value = None
    assert oauth_server.validate_auth_code("auth_code_invalid", "LEAtTrace-frontend", db=mock_db2) is False

    # Validation with wrong verifier should fail
    import datetime as _dt
    from app import models as _models
    mock_auth_code = MagicMock()
    mock_auth_code.client_id = "LEAtTrace-frontend"
    mock_auth_code.expires_at = _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None) + _dt.timedelta(minutes=5)
    mock_auth_code.used = False
    mock_auth_code.code_challenge = challenge
    mock_auth_code.code_challenge_method = "S256"
    mock_db3 = MagicMock()
    mock_db3.query.return_value.filter.return_value.first.return_value = mock_auth_code
    assert oauth_server.validate_auth_code(code, "LEAtTrace-frontend", code_verifier="wrong-verifier", db=mock_db3) is False

    # Correct verifier: dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk corresponds to E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
    mock_db4 = MagicMock()
    mock_auth_code2 = MagicMock()
    mock_auth_code2.client_id = "LEAtTrace-frontend"
    mock_auth_code2.expires_at = _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None) + _dt.timedelta(minutes=5)
    mock_auth_code2.used = False
    mock_auth_code2.code_challenge = challenge
    mock_auth_code2.code_challenge_method = "S256"
    mock_db4.query.return_value.filter.return_value.first.return_value = mock_auth_code2
    assert oauth_server.validate_auth_code(
        code, "LEAtTrace-frontend",
        code_verifier="dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        db=mock_db4,
    ) is True


def test_oidc_discovery_and_claims():
    doc = oidc_provider.get_discovery_document()
    assert doc["issuer"] == "http://localhost:8000"
    assert "jwks_uri" in doc
    
    token = oidc_provider.generate_id_token("user_101", "inspector@gov.in", "investigator", "Cybercrime")
    assert token["sub"] == "user_101"
    assert token["role"] == "investigator"

def test_refresh_token_rotation_and_reuse():
    family_id, ref_1 = refresh_service.create_family()
    
    # Initial rotation
    ref_2, acc_1 = refresh_service.rotate_token(ref_1)
    assert ref_2 != ref_1
    
    # Second rotation (using active token)
    ref_3, acc_2 = refresh_service.rotate_token(ref_2)
    assert ref_3 != ref_2
    
    # Replay attack: reusing ref_1 (used token) should revoke the family
    with pytest.raises(Exception, match="Token reuse detected"):
        refresh_service.rotate_token(ref_1)

def test_device_risk_scoring():
    ua_windows = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
    details = device_manager.parse_user_agent(ua_windows)
    assert details["os"] == "Windows"
    assert details["browser"] == "Google Chrome"
    
    # Non-trusted external user agent risk should be elevated
    risk = device_manager.evaluate_device_risk("8.8.8.8", ua_windows, False)
    assert risk >= 50

def test_session_concurrency_limit():
    user_id = "investigator_x"
    # Create 3 sessions
    session_manager.create_session("s1", user_id, "Chrome", "192.168.1.1")
    session_manager.create_session("s2", user_id, "Firefox", "192.168.1.2")
    session_manager.create_session("s3", user_id, "Edge", "192.168.1.3")
    
    active_sessions = session_manager.list_user_sessions(user_id)
    assert len(active_sessions) == 3
    
    # Adding a 4th session should terminate the oldest one (s1)
    session_manager.create_session("s4", user_id, "Safari", "192.168.1.4")
    active_sessions_updated = session_manager.list_user_sessions(user_id)
    assert len(active_sessions_updated) == 3
    assert not any(s["session_id"] == "s1" for s in active_sessions_updated)

def test_rbac_inheritance():
    # Super Admin inherits settings:edit from admin
    assert rbac_engine.has_permission("super_admin", "settings:edit") is True
    # Read-Only should not have write permissions
    assert rbac_engine.has_permission("read_only", "settings:edit") is False

def test_abac_clearance_and_location():
    user_attrs = {"clearance_level": 3, "department": "Cybercrime", "role": "investigator"}
    res_attrs = {"clearance_required": 2, "department_restriction": "Cybercrime"}
    env_attrs = {"current_hour": 14}
    
    # Match inputs
    assert abac_engine.evaluate_policy(user_attrs, res_attrs, env_attrs) is True
    
    # Low clearance level should fail
    user_attrs["clearance_level"] = 1
    assert abac_engine.evaluate_policy(user_attrs, res_attrs, env_attrs) is False
