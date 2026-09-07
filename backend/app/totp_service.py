import hmac
import hashlib
import time
import struct
import base64
import secrets
from typing import List, Dict, Any

class TOTPService:
    def generate_totp_secret(self) -> Dict[str, str]:
        """Generates a random base32 TOTP secret and returns the registration URI."""
        # 160-bit secret key (20 bytes)
        raw_secret = secrets.token_bytes(20)
        secret_b32 = base64.b32encode(raw_secret).decode("utf-8")
        
        # Standard OATH URI formatting
        label = "LEAtTrace:Investigator"
        uri = f"otpauth://totp/{label}?secret={secret_b32}&issuer=LEAtTrace&algorithm=SHA1&digits=6&period=30"
        
        return {
            "secret": secret_b32,
            "registration_uri": uri
        }

    def verify_totp_token(self, secret: str, code: str) -> bool:
        """Validates a 6-digit TOTP token against the secret using standard RFC 6238 calculations."""
        try:
            # Clean inputs
            clean_secret = secret.strip().replace(" ", "")
            clean_code = int(code.strip())
            
            # Decode key
            key = base64.b32decode(clean_secret, casefold=True)
            
            # Allow time drift window (-1 to +1 interval)
            current_time = int(time.time() / 30)
            for drift in [-1, 0, 1]:
                msg = struct.pack(">Q", current_time + drift)
                h = hmac.new(key, msg, hashlib.sha1).digest()
                o = h[19] & 15
                token = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
                if token == clean_code:
                    return True
        except Exception:
            pass
        return False

    def generate_backup_codes(self) -> List[str]:
        """Generates 8-digit secure alphanumeric backup emergency recovery codes."""
        codes = []
        for _ in range(5):
            codes.append(secrets.token_hex(4).upper()) # 8 characters hex
        return codes

totp_service = TOTPService()
