"""
Enhanced Multi-Factor Authentication Engine
Supports TOTP, WebAuthn/FIDO2, Backup Codes, and Device Fingerprinting
"""
import uuid
import secrets
import hashlib
import datetime
from typing import Optional, List, Tuple
from pydantic import BaseModel
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import pyotp
import qrcode
from io import BytesIO
import base64

# ============= TOTP / OTP Management =============

class TOTPConfig(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_base64: Optional[str] = None
    backup_codes: List[str] = []

class BackupCode(BaseModel):
    code: str
    used: bool
    used_at: Optional[datetime.datetime] = None

def generate_totp_secret() -> str:
    """Generate a cryptographically secure TOTP secret."""
    return pyotp.random_base32()

def get_totp_provisioning_uri(secret: str, email: str, issuer: str = "LEAtTrace") -> str:
    """Generate provisioning URI for QR code."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)

def generate_totp_qr_code(provisioning_uri: str) -> str:
    """Generate QR code as base64 string."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify TOTP code with time window tolerance."""
    if not secret or not code or len(code) != 6:
        return False
    
    try:
        totp = pyotp.TOTP(secret)
        # Check current and nearby time windows for robustness
        return totp.verify(code, valid_window=window)
    except Exception:
        return False

def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup codes for account recovery."""
    codes = []
    for _ in range(count):
        # Format: XXXX-XXXX-XXXX-XXXX
        code = '-'.join([secrets.token_hex(2).upper() for _ in range(4)])
        codes.append(code)
    return codes

def hash_backup_code(code: str) -> str:
    """Hash backup code for secure storage."""
    return hashlib.sha256(code.encode()).hexdigest()

# ============= WebAuthn / FIDO2 Support =============

class WebAuthnCredential(BaseModel):
    id: str
    credential_id: str
    public_key: str
    counter: int
    transports: List[str] = []
    created_at: datetime.datetime
    nickname: str = "Security Key"
    last_used: Optional[datetime.datetime] = None
    is_backup_eligible: bool = False

class WebAuthnChallenge(BaseModel):
    challenge: str
    user_id: str
    username: str
    display_name: str
    timeout: int = 60000
    attestation: str = "direct"
    user_verification: str = "required"

def generate_webauthn_challenge() -> Tuple[str, str]:
    """Generate a challenge for WebAuthn registration/authentication."""
    challenge_bytes = secrets.token_bytes(32)
    challenge_b64 = base64.b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    challenge_id = str(uuid.uuid4())
    return challenge_id, challenge_b64

def create_webauthn_registration_challenge(
    user_id: str,
    email: str,
    display_name: str
) -> WebAuthnChallenge:
    """Create a WebAuthn registration challenge."""
    _, challenge = generate_webauthn_challenge()
    
    return WebAuthnChallenge(
        challenge=challenge,
        user_id=base64.b64encode(user_id.encode()).decode(),
        username=email,
        display_name=display_name,
        timeout=120000,
        attestation="direct",
        user_verification="required"
    )

def create_webauthn_authentication_challenge(
    user_id: str,
    registered_credentials: List[str]
) -> dict:
    """Create a WebAuthn authentication challenge."""
    _, challenge = generate_webauthn_challenge()
    
    return {
        "challenge": challenge,
        "timeout": 60000,
        "userVerification": "required",
        "allowCredentials": [
            {
                "type": "public-key",
                "id": cred_id,
                "transports": ["usb", "nfc", "ble", "internal"]
            }
            for cred_id in registered_credentials
        ]
    }

# ============= Device Fingerprinting =============

class DeviceFingerprint(BaseModel):
    id: str
    user_id: str
    fingerprint_hash: str
    device_name: str
    browser: str
    os: str
    ip_address: str
    created_at: datetime.datetime
    last_seen: datetime.datetime
    is_trusted: bool = False
    trust_created_at: Optional[datetime.datetime] = None
    trust_expires_at: Optional[datetime.datetime] = None
    device_type: str = "web"  # web, mobile, desktop

def calculate_device_fingerprint(
    user_agent: str,
    ip_address: str,
    accept_language: str,
    screen_resolution: Optional[str] = None,
    timezone: Optional[str] = None
) -> str:
    """Calculate device fingerprint from browser/device information."""
    fingerprint_data = f"{user_agent}|{ip_address}|{accept_language}|{screen_resolution}|{timezone}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()

def is_device_trusted(
    device_fingerprint: DeviceFingerprint,
    current_time: datetime.datetime = None
) -> bool:
    """Check if device is currently trusted."""
    if not device_fingerprint.is_trusted:
        return False
    
    if current_time is None:
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    
    if device_fingerprint.trust_expires_at and current_time > device_fingerprint.trust_expires_at:
        return False
    
    return True

def calculate_device_risk_score(
    device_fingerprint: DeviceFingerprint,
    login_history: List[dict],
    current_location: Optional[dict] = None
) -> float:
    """
    Calculate risk score for device (0.0-1.0).
    Factors: first-time device, geographic anomaly, time-based anomaly
    """
    risk_score = 0.0
    
    # Risk: First-time device
    if device_fingerprint.created_at == device_fingerprint.last_seen:
        risk_score += 0.3
    
    # Risk: Geographic inconsistency (impossible travel)
    if current_location and len(login_history) > 0:
        last_login = login_history[-1]
        if 'location' in last_login:
            # Simple distance check (in production, use real geo-distance)
            if last_login['location'] != current_location:
                risk_score += 0.2
    
    # Risk: Device not previously trusted
    if not device_fingerprint.is_trusted:
        risk_score += 0.15
    
    return min(risk_score, 1.0)

# ============= MFA Session Management =============

class MFASession(BaseModel):
    id: str
    user_id: str
    challenge_type: str  # 'totp', 'webauthn', 'backup_code', 'sms'
    challenge_id: str
    created_at: datetime.datetime
    expires_at: datetime.datetime
    attempts: int = 0
    max_attempts: int = 3
    is_completed: bool = False
    device_fingerprint_id: Optional[str] = None

def create_mfa_session(
    user_id: str,
    challenge_type: str,
    challenge_id: str,
    duration_minutes: int = 5
) -> MFASession:
    """Create a new MFA challenge session."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    return MFASession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        challenge_type=challenge_type,
        challenge_id=challenge_id,
        created_at=now,
        expires_at=now + datetime.timedelta(minutes=duration_minutes),
        attempts=0,
        max_attempts=3,
        is_completed=False
    )

def is_mfa_session_valid(mfa_session: MFASession, current_time: datetime.datetime = None) -> bool:
    """Check if MFA session is still valid."""
    if mfa_session.is_completed:
        return False
    
    if mfa_session.attempts >= mfa_session.max_attempts:
        return False
    
    if current_time is None:
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    
    if current_time > mfa_session.expires_at:
        return False
    
    return True

# ============= MFA Policy Engine =============

class MFAPolicy(BaseModel):
    id: str
    name: str
    description: str
    required_for_roles: List[str]
    required_for_operations: List[str]  # 'case_access', 'evidence_download', 'user_management'
    grace_period_days: int = 0
    require_updated_device: bool = True
    device_trust_duration_days: int = 30
    backup_codes_count: int = 10
    enforced: bool = True
    created_at: datetime.datetime

class MFAPolicyEngine:
    """Enforce MFA policies across the platform."""
    
    @staticmethod
    def should_require_mfa(
        user_role: str,
        operation: str,
        policies: List[MFAPolicy],
        user_mfa_enabled: bool,
        device_trusted: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if MFA is required for the operation.
        Returns: (require_mfa, reason)
        """
        for policy in policies:
            if not policy.enforced:
                continue
            
            # Check role-based requirement
            if user_role in policy.required_for_roles:
                if not user_mfa_enabled:
                    return True, f"MFA required for role: {user_role}"
                if policy.require_updated_device and not device_trusted:
                    return True, "MFA required for untrusted device"
            
            # Check operation-based requirement
            if operation in policy.required_for_operations:
                if not user_mfa_enabled:
                    return True, f"MFA required for operation: {operation}"
                if policy.require_updated_device and not device_trusted:
                    return True, "MFA required for untrusted device on sensitive operation"
        
        return False, None

# ============= Default MFA Policies for LEAtTrace =============

DEFAULT_MFA_POLICIES = [
    MFAPolicy(
        id="policy_admin_enforcement",
        name="Admin MFA Enforcement",
        description="All admin operations require MFA",
        required_for_roles=["admin", "supervisor"],
        required_for_operations=["user_management", "system_configuration", "audit_access"],
        grace_period_days=0,
        require_updated_device=True,
        device_trust_duration_days=30,
        enforced=True,
        created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    ),
    MFAPolicy(
        id="policy_sensitive_operations",
        name="Sensitive Operations MFA",
        description="Sensitive operations require MFA for all users",
        required_for_roles=["admin", "supervisor", "investigator", "analyst"],
        required_for_operations=["evidence_access", "case_closure", "data_export", "evidence_download"],
        grace_period_days=7,
        require_updated_device=False,
        device_trust_duration_days=14,
        enforced=True,
        created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    ),
    MFAPolicy(
        id="policy_investigator_baseline",
        name="Investigator Baseline MFA",
        description="All investigators should have MFA enabled",
        required_for_roles=["investigator"],
        required_for_operations=[],
        grace_period_days=14,
        require_updated_device=False,
        device_trust_duration_days=30,
        enforced=True,
        created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    ),
]

# ============= MFA Engine Main Class =============

class MFAEngine:
    """Main MFA Engine for LEAtTrace."""
    
    @staticmethod
    def setup_mfa_for_user(
        user_id: str,
        email: str,
        display_name: str,
        mfa_type: str = "totp"
    ) -> dict:
        """Setup MFA for a user (TOTP or WebAuthn)."""
        if mfa_type == "totp":
            secret = generate_totp_secret()
            uri = get_totp_provisioning_uri(secret, email)
            qr_code = generate_totp_qr_code(uri)
            backup_codes = generate_backup_codes(10)
            
            return {
                "type": "totp",
                "secret": secret,
                "provisioning_uri": uri,
                "qr_code": qr_code,
                "backup_codes": backup_codes,
                "hashed_backup_codes": [hash_backup_code(code) for code in backup_codes]
            }
        
        elif mfa_type == "webauthn":
            challenge = create_webauthn_registration_challenge(user_id, email, display_name)
            return {
                "type": "webauthn",
                "challenge": challenge.dict()
            }
        
        else:
            raise ValueError(f"Unsupported MFA type: {mfa_type}")
    
    @staticmethod
    def verify_mfa_code(
        secret: str,
        code: str,
        mfa_type: str = "totp",
        backup_codes: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Verify MFA code."""
        if mfa_type == "totp":
            if verify_totp_code(secret, code):
                return True, "TOTP verification successful"
            
            # Check backup codes
            if backup_codes:
                code_hash = hash_backup_code(code)
                if code_hash in backup_codes:
                    return True, "Backup code used"
            
            return False, "Invalid TOTP or backup code"
        
        else:
            return False, "Unknown MFA type"
    
    @staticmethod
    def get_mfa_status(
        user_mfa_enabled: bool,
        device_trusted: bool,
        device_risk_score: float
    ) -> dict:
        """Get current MFA status for user."""
        return {
            "mfa_enabled": user_mfa_enabled,
            "device_trusted": device_trusted,
            "device_risk_score": device_risk_score,
            "requires_challenge": device_risk_score > 0.5 or not device_trusted,
            "recommended_action": (
                "Enable MFA" if not user_mfa_enabled else
                "Trust this device" if not device_trusted else
                "Monitor activity" if device_risk_score > 0.3 else
                "All clear"
            )
        }
