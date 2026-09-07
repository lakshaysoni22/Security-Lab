"""
Advanced Session Management with Redis Support
Features: Refresh Token Rotation, Device Tracking, Session Revocation, Session Policies
"""
import uuid
import datetime
import json
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from pydantic import BaseModel

# Note: Actual Redis integration requires redis package installation
# For now, this provides the interface/models

class SessionStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"
    IDLE_TIMEOUT = "idle_timeout"

class SessionDeviceInfo(BaseModel):
    device_id: str
    device_name: str
    device_type: str  # web, mobile, desktop, api
    browser: str
    os: str
    ip_address: str
    user_agent: str
    fingerprint: str
    trusted: bool = False
    trusted_at: Optional[datetime.datetime] = None

class TokenMetadata(BaseModel):
    token_id: str
    token_type: str  # access, refresh
    issued_at: datetime.datetime
    expires_at: datetime.datetime
    rotation_count: int = 0
    parent_token_id: Optional[str] = None  # For token rotation tracking

class SessionPolicy(BaseModel):
    """Session management policy."""
    id: str
    name: str
    
    # Token expiration
    access_token_lifetime_minutes: int = 15
    refresh_token_lifetime_days: int = 7
    
    # Refresh token rotation
    enable_refresh_token_rotation: bool = True
    rotate_on_each_use: bool = True  # Security: Rotate token every time it's used
    max_refresh_count: int = 100
    
    # Session properties
    max_sessions_per_user: int = 10
    max_sessions_per_device: int = 2
    session_timeout_minutes: int = 30  # Idle timeout
    absolute_session_timeout_hours: int = 24
    
    # Device binding
    bind_to_device: bool = True
    allow_device_change: bool = False
    device_binding_required: bool = False
    
    # Security features
    require_mfa_on_new_device: bool = True
    require_mfa_on_sensitive_operation: bool = True
    enable_session_revocation: bool = True
    enable_concurrent_session_limit: bool = True
    
    # Enforcement
    enforce_for_roles: List[str] = []
    enforced: bool = True

class SessionAnomalyEvent(BaseModel):
    """Detected session anomaly."""
    event_id: str
    session_id: str
    user_id: str
    event_type: str  # impossible_travel, concurrent_access, device_change, location_change
    severity: str  # low, medium, high, critical
    detected_at: datetime.datetime
    details: Dict[str, Any]
    action_taken: str  # log, block, require_mfa, revoke

# ============= Session Manager Core =============

class AdvancedSessionManager:
    """
    Advanced session management with Redis backend.
    Handles token rotation, device tracking, session revocation, and policies.
    """
    
    def __init__(self, redis_client=None, db_session=None):
        """Initialize session manager."""
        self.redis_client = redis_client
        self.db_session = db_session
        self.default_policies = self._get_default_policies()
    
    @staticmethod
    def _get_default_policies() -> Dict[str, SessionPolicy]:
        """Get default session policies for different user roles."""
        return {
            "admin": SessionPolicy(
                id="policy_admin",
                name="Admin Session Policy",
                access_token_lifetime_minutes=30,
                refresh_token_lifetime_days=7,
                enable_refresh_token_rotation=True,
                rotate_on_each_use=True,
                max_sessions_per_user=3,
                session_timeout_minutes=15,
                absolute_session_timeout_hours=4,
                device_binding_required=True,
                require_mfa_on_new_device=True,
                enforce_for_roles=["admin", "supervisor"]
            ),
            "investigator": SessionPolicy(
                id="policy_investigator",
                name="Investigator Session Policy",
                access_token_lifetime_minutes=60,
                refresh_token_lifetime_days=14,
                enable_refresh_token_rotation=True,
                rotate_on_each_use=False,
                max_sessions_per_user=5,
                session_timeout_minutes=60,
                absolute_session_timeout_hours=12,
                device_binding_required=False,
                require_mfa_on_new_device=False,
                enforce_for_roles=["investigator", "analyst"]
            ),
            "readonly": SessionPolicy(
                id="policy_readonly",
                name="Read-Only Session Policy",
                access_token_lifetime_minutes=120,
                refresh_token_lifetime_days=30,
                enable_refresh_token_rotation=False,
                max_sessions_per_user=10,
                session_timeout_minutes=120,
                absolute_session_timeout_hours=24,
                device_binding_required=False,
                require_mfa_on_new_device=False,
                enforce_for_roles=["readonly"]
            )
        }
    
    def get_policy_for_role(self, role: str) -> SessionPolicy:
        """Get session policy for user role."""
        return self.default_policies.get(role, self.default_policies["readonly"])
    
    def validate_session_for_operation(
        self,
        user_role: str,
        operation: str,
        session_age_seconds: float,
        is_device_trusted: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if session can perform operation.
        Returns: (is_valid, reason_if_invalid)
        """
        policy = self.get_policy_for_role(user_role)
        
        # Check absolute session timeout
        absolute_timeout_seconds = policy.absolute_session_timeout_hours * 3600
        if session_age_seconds > absolute_timeout_seconds:
            return False, f"Absolute session timeout ({policy.absolute_session_timeout_hours}h) exceeded"
        
        # Check device binding
        if policy.device_binding_required and not is_device_trusted:
            return False, "Session requires trusted device binding"
        
        # Operation-specific checks
        if operation in ["user_management", "system_configuration"]:
            if not is_device_trusted:
                return False, "Sensitive operation requires trusted device"
        
        return True, None
    
    def should_rotate_refresh_token(
        self,
        user_role: str,
        rotation_count: int,
        is_new_device: bool
    ) -> bool:
        """Determine if refresh token should be rotated."""
        policy = self.get_policy_for_role(user_role)
        
        if not policy.enable_refresh_token_rotation:
            return False
        
        if rotation_count >= policy.max_refresh_count:
            return True
        
        if is_new_device:
            return True
        
        if policy.rotate_on_each_use:
            return True
        
        return False

# ============= Session Anomaly Detection =============

class SessionAnomalyDetector:
    """Detect suspicious session behavior."""
    
    @staticmethod
    def detect_impossible_travel(
        previous_location: Dict[str, float],
        current_location: Dict[str, float],
        time_diff_seconds: float,
        max_speed_kmh: float = 900  # Plane speed
    ) -> bool:
        """
        Detect if travel between two locations is impossible.
        Returns True if travel is impossible.
        """
        import math
        
        if not previous_location or not current_location:
            return False
        
        # Simple Euclidean distance (in production use Haversine formula)
        lat1, lon1 = previous_location.get('latitude', 0), previous_location.get('longitude', 0)
        lat2, lon2 = current_location.get('latitude', 0), current_location.get('longitude', 0)
        
        distance_km = math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111  # rough conversion
        
        if time_diff_seconds == 0:
            return distance_km > 1  # Locations must be different or very close
        
        required_speed_kmh = distance_km / (time_diff_seconds / 3600)
        
        return required_speed_kmh > max_speed_kmh
    
    @staticmethod
    def detect_concurrent_access(
        sessions_data: List[Dict[str, Any]],
        time_window_minutes: int = 5
    ) -> List[Tuple[str, str]]:
        """Detect concurrent sessions from different locations."""
        conflicts = []
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        
        for i, session1 in enumerate(sessions_data):
            for session2 in sessions_data[i+1:]:
                time_diff = abs((session1.get('last_activity') - session2.get('last_activity', now)).total_seconds() / 60)
                
                if time_diff < time_window_minutes:
                    ip1 = session1.get('ip_address')
                    ip2 = session2.get('ip_address')
                    
                    if ip1 != ip2:
                        conflicts.append((session1.get('session_id'), session2.get('session_id')))
        
        return conflicts
    
    @staticmethod
    def calculate_session_risk_score(
        is_device_trusted: bool,
        session_age_seconds: float,
        token_rotation_count: int,
        last_activity_seconds: float
    ) -> float:
        """Calculate overall risk score for session (0.0-1.0)."""
        risk_score = 0.0
        
        # Risk: Device not trusted
        if not is_device_trusted:
            risk_score += 0.2
        
        # Risk: New session (< 1 minute)
        if session_age_seconds < 60:
            risk_score += 0.15
        
        # Risk: High token rotation count
        if token_rotation_count > 50:
            risk_score += 0.1
        
        # Risk: Very recent activity (< 1 second, potential abuse)
        if last_activity_seconds < 1:
            risk_score += 0.05
        
        return min(risk_score, 1.0)

# ============= Token Management =============

class TokenRotationManager:
    """Manage refresh token rotation with security best practices."""
    
    @staticmethod
    def create_rotation_metadata(
        user_id: str,
        parent_token_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create metadata for token rotation tracking."""
        return {
            "user_id": user_id,
            "token_id": f"tok_{uuid.uuid4().hex[:16]}",
            "created_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(),
            "parent_token_id": parent_token_id,
            "rotation_count": 1 if parent_token_id else 0
        }
    
    @staticmethod
    def validate_token_for_rotation(
        token_age_seconds: float,
        rotation_count: int,
        max_rotations: int = 100,
        max_age_hours: int = 24
    ) -> Tuple[bool, Optional[str]]:
        """Validate if token can be rotated."""
        if rotation_count >= max_rotations:
            return False, f"Maximum rotation count ({max_rotations}) exceeded"
        
        if token_age_seconds > (max_age_hours * 3600):
            return False, f"Token older than maximum age ({max_age_hours}h)"
        
        return True, None
    
    @staticmethod
    def compute_token_binding(
        token_value: str,
        device_fingerprint: str,
        ip_address: str
    ) -> str:
        """
        Compute token binding to prevent token theft.
        Binds token to device and IP.
        """
        binding_data = f"{token_value}:{device_fingerprint}:{ip_address}"
        return hashlib.sha256(binding_data.encode()).hexdigest()

# ============= Default Policies =============

DEFAULT_SESSION_POLICIES = {
    "admin": SessionPolicy(
        id="policy_admin",
        name="Admin Session Policy",
        access_token_lifetime_minutes=30,
        refresh_token_lifetime_days=7,
        enable_refresh_token_rotation=True,
        rotate_on_each_use=True,
        max_sessions_per_user=3,
        session_timeout_minutes=15,
        absolute_session_timeout_hours=4,
        device_binding_required=True,
        require_mfa_on_new_device=True
    ),
    "investigator": SessionPolicy(
        id="policy_investigator",
        name="Investigator Session Policy",
        access_token_lifetime_minutes=60,
        refresh_token_lifetime_days=14,
        enable_refresh_token_rotation=True,
        rotate_on_each_use=False,
        max_sessions_per_user=5,
        session_timeout_minutes=60,
        absolute_session_timeout_hours=12
    ),
    "readonly": SessionPolicy(
        id="policy_readonly",
        name="Read-Only Session Policy",
        access_token_lifetime_minutes=120,
        refresh_token_lifetime_days=30,
        enable_refresh_token_rotation=False,
        max_sessions_per_user=10,
        session_timeout_minutes=120,
        absolute_session_timeout_hours=24
    )
}
