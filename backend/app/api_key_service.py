"""
LEAtTrace IAM — API Key Service.

Enterprise API key generation, validation, rotation, and revocation.
Keys are SHA-256 hashed before storage; only the prefix is stored in cleartext.
"""

import secrets
import hashlib
import datetime
import uuid
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from . import models


class APIKeyService:
    """Manages API key lifecycle: create, validate, rotate, revoke."""

    KEY_PREFIX_LENGTH = 8
    KEY_LENGTH = 48  # Total key length in hex characters

    def create_key(
        self, db: Session, user_id: str, name: str,
        scopes: str = "read", expires_days: Optional[int] = 365
    ) -> Dict[str, Any]:
        """Generates a new API key and stores the hash."""
        raw_key = f"lt_{secrets.token_hex(self.KEY_LENGTH // 2)}"
        key_prefix = raw_key[:self.KEY_PREFIX_LENGTH]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        expires_at = None
        if expires_days:
            expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=expires_days)

        api_key = models.APIKey(
            id=str(uuid.uuid4()),
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            scopes=scopes,
            is_active=True,
            expires_at=expires_at,
        )
        db.add(api_key)
        db.commit()

        return {
            "api_key": raw_key,
            "key_prefix": key_prefix,
            "name": name,
            "scopes": scopes,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "warning": "Store this key securely. It will not be shown again.",
        }

    def validate_key(self, db: Session, raw_key: str) -> Optional[Dict[str, Any]]:
        """Validates an API key and returns the associated user info."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = db.query(models.APIKey).filter(
            models.APIKey.key_hash == key_hash,
            models.APIKey.is_active == True,
        ).first()

        if not api_key:
            return None

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
            api_key.is_active = False
            db.commit()
            return None

        # Update last used
        api_key.last_used = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        db.commit()

        return {
            "user_id": api_key.user_id,
            "name": api_key.name,
            "scopes": api_key.scopes,
            "key_prefix": api_key.key_prefix,
        }

    def revoke_key(self, db: Session, key_id: str, user_id: str) -> bool:
        """Revokes an API key."""
        api_key = db.query(models.APIKey).filter(
            models.APIKey.id == key_id,
            models.APIKey.user_id == user_id,
        ).first()

        if not api_key:
            return False

        api_key.is_active = False
        db.commit()
        return True

    def list_keys(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Lists all API keys for a user (without revealing the actual key)."""
        keys = db.query(models.APIKey).filter(
            models.APIKey.user_id == user_id,
        ).all()

        return [
            {
                "id": k.id,
                "name": k.name,
                "key_prefix": k.key_prefix,
                "scopes": k.scopes,
                "is_active": k.is_active,
                "last_used": k.last_used.isoformat() if k.last_used else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "created_at": k.created_at.isoformat() if k.created_at else None,
            }
            for k in keys
        ]

    def rotate_key(
        self, db: Session, key_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Revokes old key and creates a new one with the same settings."""
        old_key = db.query(models.APIKey).filter(
            models.APIKey.id == key_id,
            models.APIKey.user_id == user_id,
            models.APIKey.is_active == True,
        ).first()

        if not old_key:
            return None

        # Revoke old key
        old_key.is_active = False
        db.commit()

        # Create new key with same settings
        return self.create_key(
            db=db,
            user_id=user_id,
            name=old_key.name,
            scopes=old_key.scopes,
        )


api_key_service = APIKeyService()
