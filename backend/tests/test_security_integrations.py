import os
import tempfile
from pathlib import Path

from app.encryption_engine import EncryptionManager, EncryptionKey
from app.sso_federation import SSOProviderRegistry, LocalSSOProvider
from app.secret_manager import SecretManagerRegistry, LocalSecretProvider
from app.redis_session_manager import RedisSessionStore
from app.siem_integrations import SIEMIntegrationService
from app.compliance_engine import ComplianceAutomation


def test_encryption_stack_round_trip():
    manager = EncryptionManager()
    key = EncryptionKey(key_id="test-key", key_material=b"A" * 32, is_primary=True)
    assert manager.add_key(key) is True

    encrypted = manager.encrypt_sensitive_data("secret-value", context="user:1")
    assert encrypted is not None
    assert manager.decrypt_sensitive_data(encrypted, context="user:1") == "secret-value"


def test_sso_provider_authentication_and_registry():
    registry = SSOProviderRegistry()
    provider = LocalSSOProvider(name="local", users={"admin": "P@ssw0rd!"})
    registry.register(provider)

    auth = registry.authenticate("local", "admin", "P@ssw0rd!")
    assert auth is True
    assert registry.get_provider("local") is provider


def test_secret_provider_resolution():
    registry = SecretManagerRegistry()
    provider = LocalSecretProvider(name="local", values={"db.password": "s3cr3t"})
    registry.register(provider)

    resolved = registry.resolve("local", "db.password")
    assert resolved == "s3cr3t"


def test_redis_session_store_rotation_and_revoke():
    store = RedisSessionStore(use_redis=False)
    session_id = store.create_session("user-1", "device-1", refresh_token="token-1")
    assert session_id

    assert store.get_session(session_id)["refresh_token"] == "token-1"
    new_token = store.rotate_refresh_token(session_id, "token-2")
    assert new_token == "token-2"
    assert store.revoke_session(session_id) is True


def test_siem_integration_service_accepts_events():
    service = SIEMIntegrationService()
    event = service.send_event({"source": "auth", "message": "login"})
    assert event["status"] == "queued"
    assert event["event"]["source"] == "auth"


def test_compliance_scan_reports_findings(tmp_path: Path):
    target = tmp_path / "demo"
    target.mkdir()
    (target / "requirements.txt").write_text("requests==2.0.0\n", encoding="utf-8")
    (target / "secrets.txt").write_text("AKIA1234567890EXAMPLE\n", encoding="utf-8")

    automation = ComplianceAutomation()
    report = automation.scan_path(target)
    assert report["status"] == "completed"
    assert report["findings"]
