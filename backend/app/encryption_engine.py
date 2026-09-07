"""
Encryption Infrastructure for LEAtTrace
Supports AES-256-GCM, envelope encryption, key rotation
"""
import os
import json
import datetime
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import secrets
import base64

# ============= Encryption Configuration =============

ENCRYPTION_CONFIG = {
    "algorithm": "AES-256-GCM",
    "key_size": 32,  # 256 bits
    "iv_size": 12,   # 96 bits for GCM
    "tag_size": 128, # 128 bits
    "pbkdf2_iterations": 100000
}

# ============= Key Management =============

class EncryptionKey:
    """Represents an encryption key with metadata."""
    
    def __init__(
        self,
        key_id: str,
        key_material: bytes,
        algorithm: str = "AES-256-GCM",
        created_at: datetime.datetime = None,
        expires_at: Optional[datetime.datetime] = None,
        version: int = 1,
        is_primary: bool = False
    ):
        self.key_id = key_id
        self.key_material = key_material
        self.algorithm = algorithm
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        self.expires_at = expires_at
        self.version = version
        self.is_primary = is_primary
        self.rotation_count = 0
    
    def is_valid(self) -> bool:
        """Check if key is still valid."""
        if self.expires_at and datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) > self.expires_at:
            return False
        return True
    
    def serialize(self) -> str:
        """Serialize key to JSON string."""
        return json.dumps({
            "key_id": self.key_id,
            "key_material": base64.b64encode(self.key_material).decode(),
            "algorithm": self.algorithm,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "version": self.version,
            "is_primary": self.is_primary
        })

# ============= Symmetric Encryption =============

class AES256GCMEncryptor:
    """AES-256-GCM symmetric encryption."""
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a new AES-256 key."""
        return secrets.token_bytes(ENCRYPTION_CONFIG["key_size"])
    
    @staticmethod
    def generate_iv() -> bytes:
        """Generate a new IV for GCM mode."""
        return secrets.token_bytes(ENCRYPTION_CONFIG["iv_size"])
    
    @staticmethod
    def encrypt(
        plaintext: bytes,
        key: bytes,
        associated_data: Optional[bytes] = None,
        iv: Optional[bytes] = None
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt data with AES-256-GCM.
        Returns: (ciphertext, iv, tag)
        """
        if iv is None:
            iv = AES256GCMEncryptor.generate_iv()
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)
        
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return ciphertext, iv, encryptor.tag
    
    @staticmethod
    def decrypt(
        ciphertext: bytes,
        key: bytes,
        iv: bytes,
        tag: bytes,
        associated_data: Optional[bytes] = None
    ) -> Optional[bytes]:
        """
        Decrypt data with AES-256-GCM.
        Returns: plaintext or None if authentication fails
        """
        try:
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            if associated_data:
                decryptor.authenticate_additional_data(associated_data)
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext
        except Exception:
            return None

# ============= Envelope Encryption =============

class EnvelopeEncryption:
    """
    Envelope encryption: encrypts data with DEK, then encrypts DEK with KEK.
    Better key management and performance.
    """
    
    @staticmethod
    def generate_data_encryption_key() -> bytes:
        """Generate a Data Encryption Key (DEK)."""
        return AES256GCMEncryptor.generate_key()
    
    @staticmethod
    def encrypt_data_encryption_key(
        dek: bytes,
        kek: bytes
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt DEK with Key Encryption Key (KEK).
        Returns: (encrypted_dek, iv, tag)
        """
        ciphertext, iv, tag = AES256GCMEncryptor.encrypt(dek, kek)
        return ciphertext, iv, tag
    
    @staticmethod
    def decrypt_data_encryption_key(
        encrypted_dek: bytes,
        iv: bytes,
        tag: bytes,
        kek: bytes
    ) -> Optional[bytes]:
        """Decrypt DEK with KEK."""
        return AES256GCMEncryptor.decrypt(encrypted_dek, kek, iv, tag)
    
    @staticmethod
    def encrypt_with_envelope(
        plaintext: bytes,
        kek: bytes,
        associated_data: Optional[bytes] = None
    ) -> dict:
        """
        Encrypt data using envelope encryption.
        Returns: dict with encrypted_data, encrypted_dek, iv, tag, dek_iv, dek_tag
        """
        # Generate and encrypt DEK
        dek = EnvelopeEncryption.generate_data_encryption_key()
        encrypted_dek, dek_iv, dek_tag = EnvelopeEncryption.encrypt_data_encryption_key(dek, kek)
        
        # Encrypt plaintext with DEK
        ciphertext, iv, tag = AES256GCMEncryptor.encrypt(plaintext, dek, associated_data)
        
        return {
            "encrypted_data": base64.b64encode(ciphertext).decode(),
            "encrypted_dek": base64.b64encode(encrypted_dek).decode(),
            "iv": base64.b64encode(iv).decode(),
            "tag": base64.b64encode(tag).decode(),
            "dek_iv": base64.b64encode(dek_iv).decode(),
            "dek_tag": base64.b64encode(dek_tag).decode(),
            "algorithm": "AES-256-GCM-ENVELOPE",
            "kek_version": 1
        }
    
    @staticmethod
    def decrypt_with_envelope(
        encrypted_data: dict,
        kek: bytes,
        associated_data: Optional[bytes] = None
    ) -> Optional[bytes]:
        """
        Decrypt data using envelope encryption.
        """
        try:
            # Decode from base64
            ciphertext = base64.b64decode(encrypted_data["encrypted_data"])
            encrypted_dek = base64.b64decode(encrypted_data["encrypted_dek"])
            iv = base64.b64decode(encrypted_data["iv"])
            tag = base64.b64decode(encrypted_data["tag"])
            dek_iv = base64.b64decode(encrypted_data["dek_iv"])
            dek_tag = base64.b64decode(encrypted_data["dek_tag"])
            
            # Decrypt DEK
            dek = EnvelopeEncryption.decrypt_data_encryption_key(
                encrypted_dek, dek_iv, dek_tag, kek
            )
            if dek is None:
                return None
            
            # Decrypt plaintext
            plaintext = AES256GCMEncryptor.decrypt(
                ciphertext, dek, iv, tag, associated_data
            )
            return plaintext
        except Exception:
            return None

# ============= Asymmetric Encryption (RSA) =============

class RSAEncryption:
    """RSA encryption for key wrapping and digital signatures."""
    
    @staticmethod
    def generate_key_pair(key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair.
        Returns: (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    @staticmethod
    def encrypt_with_public_key(plaintext: bytes, public_key_pem: bytes) -> bytes:
        """Encrypt with public key."""
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext
    
    @staticmethod
    def decrypt_with_private_key(ciphertext: bytes, private_key_pem: bytes) -> Optional[bytes]:
        """Decrypt with private key."""
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=default_backend()
            )
            
            plaintext = private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return plaintext
        except Exception:
            return None

# ============= Key Derivation =============

class KeyDerivation:
    """Derive encryption keys from passwords."""
    
    @staticmethod
    def derive_key_from_password(
        password: str,
        salt: Optional[bytes] = None,
        iterations: int = None
    ) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.
        Returns: (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        if iterations is None:
            iterations = ENCRYPTION_CONFIG["pbkdf2_iterations"]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        
        key = kdf.derive(password.encode())
        return key, salt

# ============= Encryption Manager =============

class EncryptionManager:
    """Manage encryption operations with key rotation and versioning."""
    
    def __init__(self):
        """Initialize encryption manager."""
        self.keys: dict[str, EncryptionKey] = {}
        self.primary_key_id: Optional[str] = None
    
    def add_key(self, key: EncryptionKey) -> bool:
        """Add encryption key."""
        if key.key_id in self.keys:
            return False
        
        self.keys[key.key_id] = key
        
        if key.is_primary:
            self.primary_key_id = key.key_id
        
        return True
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Get encryption key."""
        key = self.keys.get(key_id)
        if key and key.is_valid():
            return key
        return None
    
    def get_primary_key(self) -> Optional[EncryptionKey]:
        """Get primary encryption key for new encryptions."""
        if self.primary_key_id:
            return self.get_key(self.primary_key_id)
        return None
    
    def rotate_key(self, key_id: str) -> Optional[EncryptionKey]:
        """Rotate encryption key (generate new key, mark old as deprecated)."""
        old_key = self.keys.get(key_id)
        if not old_key:
            return None
        
        # Mark old key as deprecated
        old_key.is_primary = False
        old_key.expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=30)  # Grace period
        
        # Generate new key
        new_key_material = AES256GCMEncryptor.generate_key()
        new_key_id = f"key_{datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        new_key = EncryptionKey(
            key_id=new_key_id,
            key_material=new_key_material,
            version=old_key.version + 1,
            is_primary=True
        )
        
        self.add_key(new_key)
        self.primary_key_id = new_key_id
        
        return new_key
    
    def encrypt_sensitive_data(
        self,
        data: str,
        context: Optional[str] = None
    ) -> Optional[dict]:
        """Encrypt sensitive data with current primary key."""
        key = self.get_primary_key()
        if not key:
            return None
        
        associated_data = context.encode() if context else None
        
        result = EnvelopeEncryption.encrypt_with_envelope(
            data.encode(),
            key.key_material,
            associated_data
        )
        
        result["key_id"] = key.key_id
        result["key_version"] = key.version
        
        return result
    
    def decrypt_sensitive_data(
        self,
        encrypted_data: dict,
        context: Optional[str] = None
    ) -> Optional[str]:
        """Decrypt sensitive data."""
        key_id = encrypted_data.get("key_id")
        key = self.get_key(key_id)
        if not key:
            return None
        
        associated_data = context.encode() if context else None
        
        plaintext = EnvelopeEncryption.decrypt_with_envelope(
            encrypted_data,
            key.key_material,
            associated_data
        )
        
        if plaintext:
            return plaintext.decode()
        
        return None

# ============= Field-Level Encryption for Database =============

class DatabaseFieldEncryption:
    """Encrypt specific database fields."""
    
    @staticmethod
    def encrypt_field(
        value: str,
        encryption_manager: EncryptionManager,
        field_name: str
    ) -> str:
        """Encrypt database field value."""
        encrypted = encryption_manager.encrypt_sensitive_data(value, field_name)
        if encrypted:
            return json.dumps(encrypted)
        return value
    
    @staticmethod
    def decrypt_field(
        encrypted_value: str,
        encryption_manager: EncryptionManager,
        field_name: str
    ) -> Optional[str]:
        """Decrypt database field value."""
        try:
            encrypted_dict = json.loads(encrypted_value)
            return encryption_manager.decrypt_sensitive_data(encrypted_dict, field_name)
        except Exception:
            return None
