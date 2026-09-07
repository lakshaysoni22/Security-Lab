"""
LEAtTrace IAM — JWKS Service.

RSA key pair generation, JWKS endpoint support, and RS256 JWT signing.
Provides real cryptographic key material instead of mock JWKS keys.
"""

import os
import json
import datetime
import base64
from typing import Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


class JWKSService:
    """Manages RSA key pairs and provides JWKS endpoint data."""

    def __init__(self, key_dir: str = "models_registry/keys"):
        self.key_dir = key_dir
        self._private_key = None
        self._public_key = None
        self._kid = "LEAtTrace-rsa-v1"
        os.makedirs(self.key_dir, exist_ok=True)
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Loads existing RSA keys or generates a new pair."""
        priv_path = os.path.join(self.key_dir, "rsa_private.pem")
        pub_path = os.path.join(self.key_dir, "rsa_public.pem")

        if os.path.exists(priv_path) and os.path.exists(pub_path):
            with open(priv_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(f.read(), password=None)
            with open(pub_path, "rb") as f:
                self._public_key = serialization.load_pem_public_key(f.read())
        else:
            self._private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )
            self._public_key = self._private_key.public_key()

            # Persist keys
            with open(priv_path, "wb") as f:
                f.write(self._private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            with open(pub_path, "wb") as f:
                f.write(self._public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ))

    def get_jwks(self) -> Dict[str, Any]:
        """Returns the JSON Web Key Set containing the public RSA key."""
        public_numbers = self._public_key.public_numbers()

        # Convert modulus and exponent to Base64url encoding
        n_bytes = public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, byteorder="big")
        e_bytes = public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, byteorder="big")

        n_b64 = base64.urlsafe_b64encode(n_bytes).rstrip(b"=").decode("utf-8")
        e_b64 = base64.urlsafe_b64encode(e_bytes).rstrip(b"=").decode("utf-8")

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "alg": "RS256",
                    "kid": self._kid,
                    "n": n_b64,
                    "e": e_b64,
                }
            ]
        }

    def get_private_key_pem(self) -> str:
        """Returns the private key in PEM format for JWT signing."""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

    def get_public_key_pem(self) -> str:
        """Returns the public key in PEM format for JWT verification."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    def get_kid(self) -> str:
        return self._kid


# Singleton instance
jwks_service = JWKSService()
