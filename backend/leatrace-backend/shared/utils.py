import os
import datetime
import base64
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from config.settings import settings
from shared.logger import logger

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# --- 1. Password and JWT Token Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None

# --- 2. AES Encryption / Decryption with Fallback ---
AES_KEY = os.getenv("AES_SECRET_KEY", "16byte_secretkey!").encode('utf-8')[:16]

try:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    
    def encrypt_data(plain_text: str) -> str:
        cipher = AES.new(AES_KEY, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode('utf-8'))
        # Concat nonce, tag and ciphertext
        encoded = base64.b64encode(nonce + tag + ciphertext).decode('utf-8')
        return encoded

    def decrypt_data(cipher_text: str) -> str:
        raw = base64.b64decode(cipher_text.encode('utf-8'))
        nonce = raw[:16]
        tag = raw[16:32]
        ciphertext = raw[32:]
        cipher = AES.new(AES_KEY, AES.MODE_EAX, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode('utf-8')

except ImportError:
    logger.warning("pycryptodome not installed. Fallback to basic base64 XOR encryption.")
    
    def encrypt_data(plain_text: str) -> str:
        # Basic XOR for offline testing fallback
        key_len = len(AES_KEY)
        xor_bytes = bytes([ord(c) ^ AES_KEY[i % key_len] for i, c in enumerate(plain_text)])
        return base64.b64encode(xor_bytes).decode('utf-8')

    def decrypt_data(cipher_text: str) -> str:
        raw = base64.b64decode(cipher_text.encode('utf-8'))
        key_len = len(AES_KEY)
        xor_bytes = bytes([b ^ AES_KEY[i % key_len] for i, b in enumerate(raw)])
        return xor_bytes.decode('utf-8')
