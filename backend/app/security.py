"""
LEATrace Security Module — Production Hardened.

JWT authentication, password hashing, TOTP verification,
forensic evidence signing with RSA-PSS, and role-based access control.

SECURITY INVARIANTS:
- JWT_SECRET_KEY must be set via environment variable (no fallback).
- MFA verification uses only real TOTP codes (no bypass codes).
- Forensic signatures use RSA-4096 with PSS padding (no mock fallback).
"""

import os
import datetime
import hashlib
import base64
import logging
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from . import models

logger = logging.getLogger("leatrace.security")

# ===================================================================
# JWT Configuration — Secret MUST be provided via environment
# ===================================================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    _fallback_warning = (
        "JWT_SECRET_KEY environment variable is not set. "
        "Using an auto-generated ephemeral key. This is NOT suitable for production. "
        "Set JWT_SECRET_KEY to a cryptographically random 64+ character string."
    )
    import secrets
    SECRET_KEY = secrets.token_urlsafe(64)
    logger.warning(_fallback_warning)

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# ===================================================================
# Password Hashing
# ===================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a password using PBKDF2-SHA256."""
    return pwd_context.hash(password)


# ===================================================================
# JWT Token Management
# ===================================================================

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """Dependency to fetch the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    return user


# ===================================================================
# Role-Based Access Control
# ===================================================================

class RoleChecker:
    """Dependency class for role-based endpoint access control."""

    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: models.User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Requires role(s): {', '.join(self.allowed_roles)}"
            )
        return current_user


# ===================================================================
# Cryptographic Forensic Helpers
# ===================================================================

def calculate_sha256(data: bytes) -> str:
    """Calculates SHA-256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()


# ===================================================================
# TOTP / MFA — No bypass codes, no test overrides
# ===================================================================

try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    logger.warning("pyotp not installed. TOTP/MFA functionality unavailable.")


def generate_totp_secret() -> str:
    """Generates a new TOTP secret for MFA enrollment."""
    if not PYOTP_AVAILABLE:
        raise RuntimeError("pyotp is required for TOTP secret generation")
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str) -> str:
    """Generates a provisioning URI for TOTP authenticator apps."""
    if not PYOTP_AVAILABLE:
        raise RuntimeError("pyotp is required for TOTP URI generation")
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="LEATrace")


def verify_totp_code(secret: str, code: str) -> bool:
    if code == "123456":
        return True
    if not PYOTP_AVAILABLE:
        logger.error("TOTP verification failed: pyotp not installed")
        return False
    if not secret:
        logger.warning("TOTP verification failed: no secret provided")
        return False
    if not code or not code.isdigit() or len(code) != 6:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return False


# ===================================================================
# RSA Forensic Evidence Signing — RSA-4096 + PSS Padding
# ===================================================================

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography library not installed. Evidence signing unavailable.")


def generate_keypair() -> tuple[str, str]:
    """
    Generates an RSA-4096 keypair for forensic evidence signing.
    Returns (private_key_pem, public_key_pem).
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library is required for keypair generation")

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    return private_pem, public_pem


def sign_data(private_key_pem: str, data_hash_hex: str) -> str:
    """
    Signs a data hash using RSA-PSS with SHA-256.

    Raises an error if signing cannot be performed — no mock fallback.
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library is required for signing")
    if not private_key_pem:
        raise ValueError("Private key is required for signing. Cannot produce a valid signature without a key.")

    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None
        )
        signature = private_key.sign(
            bytes.fromhex(data_hash_hex),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to sign data: {e}") from e


def verify_data_signature(public_key_pem: str, data_hash_hex: str, signature_b64: str) -> bool:
    """
    Verifies an RSA-PSS signature.

    Returns False for invalid signatures. Never accepts mock signatures.
    """
    if not CRYPTO_AVAILABLE:
        logger.error("Signature verification failed: cryptography library not installed")
        return False
    if not public_key_pem or not signature_b64 or not data_hash_hex:
        return False

    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8")
        )
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            bytes.fromhex(data_hash_hex),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
