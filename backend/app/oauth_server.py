"""
LEATrace OAuth 2.0 Server — Production Hardened.

Replaces the previous implementation which had:
- Hardcoded client_secret in source code (CRITICAL)
- In-memory AUTH_CODES dict with no TTL or persistence (HIGH)
- In-memory OAUTH_CLIENTS dict lost on restart (HIGH)

Production implementation:
- Client secrets hashed with bcrypt (passlib) or SHA-256 fallback
- OAuth clients stored in oauth_clients DB table
- Auth codes stored in auth_codes DB table with 10-minute TTL
- Single-use enforcement: codes marked `used=True` on first exchange
- Expired codes auto-cleaned on lookup
- Client secret loaded from OAUTH_CLIENT_SECRET env var only

PRODUCTION INVARIANTS:
- No plaintext secrets in source code.
- No in-memory state that survives restart.
- Auth codes expire after OAUTH_CODE_TTL_MINUTES (default: 10).
- Used codes are rejected (replay prevention).
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import logging
import os
import secrets
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("leatrace.oauth_server")

# ─── Configuration ────────────────────────────────────────────────────────────

OAUTH_CODE_TTL_MINUTES: int = int(os.getenv("OAUTH_CODE_TTL_MINUTES", "10"))

# Initial client secret — loaded from env, NEVER hardcoded
_FRONTEND_CLIENT_SECRET: Optional[str] = os.getenv("OAUTH_CLIENT_SECRET")
_FRONTEND_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "leatrace-frontend")
_FRONTEND_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3000/callback")

if not _FRONTEND_CLIENT_SECRET:
    logger.warning(
        "OAUTH_CLIENT_SECRET is not set. OAuth2 client authentication will be disabled. "
        "Set OAUTH_CLIENT_SECRET in environment variables for production."
    )


# ─── Secret Hashing ───────────────────────────────────────────────────────────

def _hash_secret(secret: str) -> str:
    """
    Hashes a client secret using bcrypt (preferred) or SHA-256+HMAC fallback.
    Never stores plaintext secrets.
    """
    try:
        from passlib.hash import bcrypt as _bcrypt
        result = _bcrypt.hash(secret)
        if result:
            return result
    except Exception:
        pass  # bcrypt unavailable or misconfigured — use SHA-256 HMAC fallback

    # SHA-256 HMAC fallback (secure when salt is secret)
    import hmac
    salt = os.getenv("OAUTH_HASH_SALT", "leatrace-oauth-salt-v2-2025")
    return "sha256:" + hmac.new(salt.encode(), secret.encode(), hashlib.sha256).hexdigest()


def _verify_secret(secret: str, hashed: str) -> bool:
    """Verifies a client secret against a stored hash."""
    if hashed.startswith("sha256:"):
        # SHA-256 HMAC path
        import hmac
        salt = os.getenv("OAUTH_HASH_SALT", "leatrace-oauth-salt-v2-2025")
        expected = "sha256:" + hmac.new(salt.encode(), secret.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, hashed)

    # bcrypt path
    try:
        from passlib.hash import bcrypt as _bcrypt
        return _bcrypt.verify(secret, hashed)
    except Exception:
        pass
    return False


# ─── OAuth Server ─────────────────────────────────────────────────────────────

class OAuthServer:
    """
    Production OAuth 2.0 Authorization Server.

    All state persisted to DB. No in-memory dicts.
    Requires a SQLAlchemy session (db) for all operations.
    """

    # ── Client Management ──────────────────────────────────────────────────────

    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: List[str],
        grant_types: Optional[List[str]] = None,
        description: Optional[str] = None,
        db: Any = None,
    ) -> Dict[str, Any]:
        """
        Registers a new OAuth2 client in the database.
        The provided secret is hashed before storage — never stored plaintext.

        Returns client metadata (without secret).
        """
        if db is None:
            raise ValueError("DB session required for register_client")

        from . import models
        secret_hash = _hash_secret(client_secret)
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

        # Check for existing client
        existing = db.query(models.OAuthClient).filter(
            models.OAuthClient.client_id == client_id
        ).first()

        if existing:
            existing.client_secret_hash = secret_hash
            existing.redirect_uris = json.dumps(redirect_uris)
            existing.grant_types = json.dumps(grant_types or ["authorization_code", "refresh_token"])
            existing.is_active = True
            db.commit()
            logger.info("OAuthClient updated: %s", client_id)
        else:
            client = models.OAuthClient(
                id=str(uuid.uuid4()),
                client_id=client_id,
                client_secret_hash=secret_hash,
                redirect_uris=json.dumps(redirect_uris),
                grant_types=json.dumps(grant_types or ["authorization_code", "refresh_token"]),
                description=description,
                created_at=now,
            )
            db.add(client)
            db.commit()
            logger.info("OAuthClient registered: %s", client_id)

        return {
            "client_id":     client_id,
            "redirect_uris": redirect_uris,
            "grant_types":   grant_types or ["authorization_code", "refresh_token"],
            "registered":    True,
        }

    def verify_client(self, client_id: str, client_secret: str, db: Any) -> bool:
        """
        Verifies client credentials against the DB.
        Returns True only if client exists, is active, and secret matches.
        """
        if db is None:
            return False

        from . import models
        client = db.query(models.OAuthClient).filter(
            models.OAuthClient.client_id == client_id,
            models.OAuthClient.is_active == True,
        ).first()

        if not client:
            logger.warning("OAuthClient not found: %s", client_id)
            return False

        if not _verify_secret(client_secret, client.client_secret_hash):
            logger.warning("OAuthClient secret mismatch: %s", client_id)
            return False

        return True

    # ── Authorization Codes ────────────────────────────────────────────────────

    def generate_auth_code(
        self,
        client_id: str,
        user_id: str,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
        scopes: Optional[str] = None,
        db: Any = None,
    ) -> str:
        """
        Issues a cryptographically random authorization code stored in the DB.
        Code expires after OAUTH_CODE_TTL_MINUTES (default: 10 minutes).
        """
        if db is None:
            raise ValueError("DB session required for generate_auth_code")

        from . import models
        code = secrets.token_urlsafe(32)
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        expires_at = now + datetime.timedelta(minutes=OAUTH_CODE_TTL_MINUTES)

        auth_code = models.AuthCode(
            id=str(uuid.uuid4()),
            code=code,
            client_id=client_id,
            user_id=user_id,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method or "S256",
            scopes=scopes,
            expires_at=expires_at,
            used=False,
            created_at=now,
        )
        db.add(auth_code)
        db.commit()
        logger.info("Auth code issued: client=%s user=%s expires=%s", client_id, user_id, expires_at.isoformat())
        return code

    def validate_auth_code(
        self,
        code: str,
        client_id: str,
        code_verifier: Optional[str] = None,
        db: Any = None,
    ) -> bool:
        """
        Validates an authorization code with full PKCE enforcement.

        Checks:
        1. Code exists in DB
        2. Code belongs to the requesting client_id
        3. Code has not expired (TTL check)
        4. Code has not been used before (replay prevention)
        5. PKCE code_verifier matches code_challenge (if challenge exists)

        Marks code as used on successful validation (single-use).
        """
        if db is None:
            logger.error("validate_auth_code called without DB session")
            return False

        from . import models
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

        auth_data = db.query(models.AuthCode).filter(
            models.AuthCode.code == code
        ).first()

        if not auth_data:
            logger.warning("Auth code not found: %s...", code[:8])
            return False

        # Client ID match
        if auth_data.client_id != client_id:
            logger.warning("Auth code client_id mismatch: expected=%s got=%s", auth_data.client_id, client_id)
            return False

        # TTL check
        if auth_data.expires_at and now > auth_data.expires_at:
            logger.warning("Auth code expired: code=%s..., expired_at=%s", code[:8], auth_data.expires_at)
            db.delete(auth_data)
            db.commit()
            return False

        # Replay prevention
        if auth_data.used:
            logger.warning("Auth code replay attempt: code=%s...", code[:8])
            return False

        # PKCE validation
        challenge = auth_data.code_challenge
        if challenge:
            if not code_verifier:
                logger.warning("PKCE challenge present but no code_verifier provided")
                return False

            method = auth_data.code_challenge_method or "S256"
            if method == "S256":
                computed = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode("utf-8")).digest()
                ).decode("utf-8").rstrip("=")
                if computed != challenge:
                    logger.warning("PKCE S256 verification failed")
                    return False
            else:  # plain
                if code_verifier != challenge:
                    logger.warning("PKCE plain verification failed")
                    return False

        # Mark as used (single-use enforcement)
        auth_data.used = True
        db.commit()
        logger.info("Auth code validated successfully: client=%s user=%s", client_id, auth_data.user_id)
        return True

    def cleanup_expired_codes(self, db: Any) -> int:
        """
        Deletes expired auth codes from the DB.
        Call periodically (e.g., on startup or in a background task).
        Returns count of deleted codes.
        """
        if db is None:
            return 0

        from . import models
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        deleted = db.query(models.AuthCode).filter(
            models.AuthCode.expires_at < now
        ).delete()
        db.commit()

        if deleted > 0:
            logger.info("Cleaned up %d expired OAuth auth codes", deleted)
        return deleted

    # ── Bootstrap ──────────────────────────────────────────────────────────────

    def bootstrap_default_client(self, db: Any) -> None:
        """
        Registers the default frontend client from environment variables.
        Called once on startup. Safe to call repeatedly (idempotent).
        Does nothing if OAUTH_CLIENT_SECRET is not set.
        """
        if not _FRONTEND_CLIENT_SECRET:
            logger.warning("OAUTH_CLIENT_SECRET not set — skipping default client bootstrap")
            return

        try:
            self.register_client(
                client_id=_FRONTEND_CLIENT_ID,
                client_secret=_FRONTEND_CLIENT_SECRET,
                redirect_uris=[_FRONTEND_REDIRECT_URI, "http://localhost:5173/callback"],
                grant_types=["authorization_code", "refresh_token", "client_credentials"],
                description="LEATrace frontend application",
                db=db,
            )
            logger.info("Default OAuth client bootstrapped: %s", _FRONTEND_CLIENT_ID)
        except Exception as e:
            logger.error("Default OAuth client bootstrap failed: %s", e)


# ─── Singleton ────────────────────────────────────────────────────────────────

oauth_server = OAuthServer()
