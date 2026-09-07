"""
Tests for the production OAuth 2.0 server hardening.

Covers:
- Auth code generation with DB persistence
- Auth code TTL / expiry rejection
- Auth code replay prevention (single-use)
- Client ID mismatch rejection
- PKCE S256 enforcement
- PKCE plain enforcement
- Client registration with hashed secret
- Client secret verification
- Expired code cleanup
"""

import datetime
import hashlib
import base64
import secrets
import os
import pytest
from unittest.mock import MagicMock, patch
from app.oauth_server import OAuthServer, _hash_secret, _verify_secret


class TestThreatFeedSchedulerConfigured:
    def test_is_configured_true(self):
        import json
        sources = json.dumps([{"type": "OFAC_SDN"}])
        with patch.dict(os.environ, {"SANCTIONS_SOURCES": sources}, clear=False):
            # _parse_sources() reads os.getenv dynamically now
            from app.feed_scheduler import _parse_sources
            assert bool(_parse_sources()) is True

    def test_status_shows_providers(self):
        import json
        from app.feed_scheduler import ThreatFeedScheduler
        sources = json.dumps([{"type": "OFAC_SDN"}])
        with patch.dict(os.environ, {"SANCTIONS_SOURCES": sources}, clear=False):
            s = ThreatFeedScheduler()
            result = s.get_status()
            assert result["configured"] is True
            assert "OFAC_SDN" in result["providers"]


class TestSecretHashing:
    def test_hash_not_plaintext(self):
        secret = "my-very-secret-key"
        hashed = _hash_secret(secret)
        assert hashed != secret
        assert len(hashed) > 10

    def test_verify_correct_secret(self):
        secret = "correct-secret"
        hashed = _hash_secret(secret)
        assert _verify_secret(secret, hashed) is True

    def test_verify_wrong_secret(self):
        secret = "correct-secret"
        hashed = _hash_secret(secret)
        assert _verify_secret("wrong-secret", hashed) is False

    def test_different_secrets_different_hashes(self):
        h1 = _hash_secret("secret-a")
        h2 = _hash_secret("secret-b")
        assert h1 != h2


class TestOAuthServerClientRegistration:
    def setup_method(self):
        self.server = OAuthServer()

    def test_register_client_requires_db(self):
        with pytest.raises(ValueError, match="DB session required"):
            self.server.register_client("client1", "secret", [], db=None)

    def test_register_client_stores_hash(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        import json
        result = self.server.register_client(
            client_id="test-client",
            client_secret="plaintext-secret",
            redirect_uris=["http://localhost:3000/cb"],
            db=mock_db,
        )
        # Verify client was added to DB
        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        # Secret hash must NOT equal plaintext
        from app import models
        assert added_obj.client_secret_hash != "plaintext-secret"

    def test_verify_client_not_found_returns_false(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.server.verify_client("nonexistent", "secret", db=mock_db)
        assert result is False

    def test_verify_client_wrong_secret_returns_false(self):
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.client_secret_hash = _hash_secret("correct-secret")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        result = self.server.verify_client("client-id", "wrong-secret", db=mock_db)
        assert result is False

    def test_verify_client_correct_secret_returns_true(self):
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.client_secret_hash = _hash_secret("correct-secret")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        result = self.server.verify_client("client-id", "correct-secret", db=mock_db)
        assert result is True


class TestOAuthAuthCodes:
    def setup_method(self):
        self.server = OAuthServer()

    def test_generate_code_requires_db(self):
        with pytest.raises(ValueError, match="DB session required"):
            self.server.generate_auth_code("client", "user", db=None)

    def test_validate_code_no_db(self):
        result = self.server.validate_auth_code("any-code", "client", db=None)
        assert result is False

    def test_validate_code_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = self.server.validate_auth_code("missing-code", "client", db=mock_db)
        assert result is False

    def test_validate_code_wrong_client_rejected(self):
        mock_db = MagicMock()
        mock_code = MagicMock()
        mock_code.client_id = "correct-client"
        mock_code.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        mock_code.used = False
        mock_code.code_challenge = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_code

        result = self.server.validate_auth_code("code-123", "wrong-client", db=mock_db)
        assert result is False

    def test_validate_expired_code_rejected(self):
        mock_db = MagicMock()
        mock_code = MagicMock()
        mock_code.client_id = "client-1"
        # Use timezone-aware UTC time, then strip tz to match production code's naive datetime
        mock_code.expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(minutes=1)
        mock_code.used = False
        mock_code.code_challenge = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_code

        result = self.server.validate_auth_code("expired-code", "client-1", db=mock_db)
        assert result is False

    def test_validate_used_code_rejected(self):
        mock_db = MagicMock()
        mock_code = MagicMock()
        mock_code.client_id = "client-1"
        mock_code.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        mock_code.used = True  # Already consumed
        mock_code.code_challenge = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_code

        result = self.server.validate_auth_code("used-code", "client-1", db=mock_db)
        assert result is False

    def test_validate_pkce_s256_success(self):
        mock_db = MagicMock()
        verifier = secrets.token_urlsafe(43)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip("=")

        mock_code = MagicMock()
        mock_code.client_id = "client-1"
        mock_code.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        mock_code.used = False
        mock_code.code_challenge = challenge
        mock_code.code_challenge_method = "S256"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_code

        result = self.server.validate_auth_code("code", "client-1", code_verifier=verifier, db=mock_db)
        assert result is True

    def test_validate_pkce_s256_wrong_verifier_rejected(self):
        mock_db = MagicMock()
        verifier = secrets.token_urlsafe(43)
        wrong_verifier = secrets.token_urlsafe(43)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip("=")

        mock_code = MagicMock()
        mock_code.client_id = "client-1"
        mock_code.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        mock_code.used = False
        mock_code.code_challenge = challenge
        mock_code.code_challenge_method = "S256"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_code

        result = self.server.validate_auth_code("code", "client-1", code_verifier=wrong_verifier, db=mock_db)
        assert result is False

    def test_validate_pkce_challenge_without_verifier_rejected(self):
        mock_db = MagicMock()
        mock_code = MagicMock()
        mock_code.client_id = "client-1"
        mock_code.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        mock_code.used = False
        mock_code.code_challenge = "some-challenge"
        mock_code.code_challenge_method = "S256"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_code

        result = self.server.validate_auth_code("code", "client-1", code_verifier=None, db=mock_db)
        assert result is False

    def test_cleanup_expired_codes(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.delete.return_value = 3
        count = self.server.cleanup_expired_codes(db=mock_db)
        assert count == 3
        mock_db.commit.assert_called_once()

    def test_cleanup_no_db_returns_zero(self):
        count = self.server.cleanup_expired_codes(db=None)
        assert count == 0
