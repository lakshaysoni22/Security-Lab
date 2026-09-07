"""
API Security Module
Rate limiting, IP whitelisting, API key management, geo-blocking
"""
import time
import datetime
import secrets
import hashlib
from typing import Optional, List, Dict, Tuple
from enum import Enum
from pydantic import BaseModel
from collections import defaultdict

# ============= Enums =============

class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    INACTIVE = "inactive"

class RateLimitType(str, Enum):
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"

# ============= Models =============

class APIKey(BaseModel):
    """API Key for service-to-service authentication."""
    key_id: str
    key_value: str
    key_hash: str  # SHA256 hash for secure storage
    name: str
    description: Optional[str] = None
    
    # Permissions
    allowed_endpoints: List[str] = []  # Empty = all endpoints
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    
    # Status
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    created_at: datetime.datetime
    last_used_at: Optional[datetime.datetime] = None
    expires_at: Optional[datetime.datetime] = None
    
    # Rate limits
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    # IP restriction
    allowed_ips: List[str] = []  # Empty = no IP restriction
    
    # Rotation
    rotation_at: Optional[datetime.datetime] = None

class RateLimitPolicy(BaseModel):
    """Rate limiting policy."""
    id: str
    name: str
    
    # Limit configuration
    limit_type: RateLimitType
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    
    # Scope
    applies_to_endpoints: List[str]
    applies_to_users: List[str] = []  # Empty = all users
    applies_to_ips: List[str] = []  # Empty = all IPs
    
    # Action on limit exceeded
    action: str = "block"  # block, throttle, warn
    
    active: bool = True
    created_at: datetime.datetime

class GeoBlockingRule(BaseModel):
    """Geographic blocking rule."""
    id: str
    rule_type: str  # whitelist, blacklist
    countries: List[str]  # ISO 3166-1 alpha-2 codes
    
    # Scope
    applies_to_endpoints: List[str]
    applies_to_operations: List[str]
    
    enabled: bool = True
    created_at: datetime.datetime

class IPWhitelistEntry(BaseModel):
    """IP whitelist entry."""
    id: str
    ip_address: str  # CIDR notation supported
    description: str
    
    # Scope
    applies_to_endpoints: List[str]  # Empty = all
    
    # Metadata
    added_by: str
    added_at: datetime.datetime
    expires_at: Optional[datetime.datetime] = None
    active: bool = True

# ============= Rate Limiter =============

class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.buckets: Dict[str, dict] = defaultdict(lambda: {
            "tokens": 0,
            "last_refill": time.time()
        })
        self.policies: Dict[str, RateLimitPolicy] = {}
    
    def add_policy(self, policy: RateLimitPolicy) -> bool:
        """Add rate limiting policy."""
        if policy.id in self.policies:
            return False
        
        self.policies[policy.id] = policy
        return True
    
    def check_rate_limit(
        self,
        identifier: str,  # user_id, ip_address, or endpoint
        requests_allowed_per_minute: int = 60,
        requests_allowed_per_hour: int = 1000
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request should be rate limited.
        Returns: (allowed, remaining_requests_info)
        """
        bucket_key_minute = f"{identifier}:minute"
        bucket_key_hour = f"{identifier}:hour"
        
        now = time.time()
        
        # Per-minute check
        minute_bucket = self.buckets[bucket_key_minute]
        if now - minute_bucket["last_refill"] > 60:
            minute_bucket["tokens"] = requests_allowed_per_minute
            minute_bucket["last_refill"] = now
        
        if minute_bucket["tokens"] <= 0:
            return False, {
                "remaining_requests_minute": 0,
                "remaining_requests_hour": self.buckets[bucket_key_hour].get("tokens", 0),
                "reset_at_minute": minute_bucket["last_refill"] + 60,
                "reason": "Rate limit exceeded (per minute)"
            }
        
        minute_bucket["tokens"] -= 1
        
        # Per-hour check
        hour_bucket = self.buckets[bucket_key_hour]
        if now - hour_bucket["last_refill"] > 3600:
            hour_bucket["tokens"] = requests_allowed_per_hour
            hour_bucket["last_refill"] = now
        
        if hour_bucket["tokens"] <= 0:
            return False, {
                "remaining_requests_minute": minute_bucket["tokens"],
                "remaining_requests_hour": 0,
                "reset_at_hour": hour_bucket["last_refill"] + 3600,
                "reason": "Rate limit exceeded (per hour)"
            }
        
        hour_bucket["tokens"] -= 1
        
        return True, {
            "remaining_requests_minute": minute_bucket["tokens"],
            "remaining_requests_hour": hour_bucket["tokens"],
            "reset_at_minute": minute_bucket["last_refill"] + 60,
            "reset_at_hour": hour_bucket["last_refill"] + 3600
        }
    
    def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limit for identifier."""
        self.buckets.pop(f"{identifier}:minute", None)
        self.buckets.pop(f"{identifier}:hour", None)
        return True

# ============= API Key Manager =============

class APIKeyManager:
    """Manage API keys for service-to-service authentication."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.api_keys: Dict[str, APIKey] = {}
        self.key_hash_map: Dict[str, str] = {}  # Hash to key_id
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_api_key(
        self,
        name: str,
        description: Optional[str] = None,
        allowed_endpoints: List[str] = None,
        requests_per_minute: int = 60,
        expires_in_days: Optional[int] = None
    ) -> APIKey:
        """Create new API key."""
        key_value = self.generate_api_key()
        key_hash = self.hash_api_key(key_value)
        
        key_id = f"key_{secrets.token_hex(8)}"
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=expires_in_days)
        
        api_key = APIKey(
            key_id=key_id,
            key_value=key_value,
            key_hash=key_hash,
            name=name,
            description=description,
            allowed_endpoints=allowed_endpoints or [],
            requests_per_minute=requests_per_minute,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            expires_at=expires_at
        )
        
        self.api_keys[key_id] = api_key
        self.key_hash_map[key_hash] = key_id
        
        return api_key
    
    def validate_api_key(
        self,
        api_key_value: str,
        endpoint: str = None,
        method: str = "GET"
    ) -> Tuple[bool, Optional[str], Optional[APIKey]]:
        """
        Validate API key.
        Returns: (is_valid, reason, api_key)
        """
        key_hash = self.hash_api_key(api_key_value)
        key_id = self.key_hash_map.get(key_hash)
        
        if not key_id:
            return False, "Invalid API key", None
        
        api_key = self.api_keys.get(key_id)
        if not api_key:
            return False, "API key not found", None
        
        # Check status
        if api_key.status == APIKeyStatus.REVOKED:
            return False, "API key revoked", None
        
        if api_key.status == APIKeyStatus.INACTIVE:
            return False, "API key inactive", None
        
        # Check expiration
        if api_key.expires_at and datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) > api_key.expires_at:
            return False, "API key expired", None
        
        # Check endpoint access
        if api_key.allowed_endpoints and endpoint and endpoint not in api_key.allowed_endpoints:
            return False, f"API key not allowed for endpoint: {endpoint}", None
        
        # Check method access
        if method not in api_key.allowed_methods:
            return False, f"API key not allowed for method: {method}", None
        
        # Update last used
        api_key.last_used_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        
        return True, None, api_key
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key."""
        if key_id not in self.api_keys:
            return False
        
        self.api_keys[key_id].status = APIKeyStatus.REVOKED
        return True
    
    def rotate_api_key(self, key_id: str) -> Optional[Tuple[APIKey, APIKey]]:
        """
        Rotate API key (generate new one, keep old until expiry).
        Returns: (old_key, new_key)
        """
        old_key = self.api_keys.get(key_id)
        if not old_key:
            return None
        
        # Create new key with same settings
        new_key = self.create_api_key(
            name=f"{old_key.name} (rotated)",
            description=old_key.description,
            allowed_endpoints=old_key.allowed_endpoints,
            requests_per_minute=old_key.requests_per_minute
        )
        
        # Mark old key for rotation (grace period of 24 hours)
        old_key.rotation_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=24)
        
        return old_key, new_key
    
    def check_ip_restriction(
        self,
        key_id: str,
        client_ip: str
    ) -> bool:
        """Check if client IP is allowed for API key."""
        api_key = self.api_keys.get(key_id)
        if not api_key or not api_key.allowed_ips:
            return True  # No restriction
        
        # Simple IP matching (in production, use ipaddress library for CIDR)
        return client_ip in api_key.allowed_ips

# ============= IP Whitelist Manager =============

class IPWhitelistManager:
    """Manage IP whitelist for platform access."""
    
    def __init__(self):
        """Initialize IP whitelist manager."""
        self.whitelist: Dict[str, IPWhitelistEntry] = {}
    
    def add_to_whitelist(
        self,
        ip_address: str,
        description: str,
        endpoints: List[str] = None,
        added_by: str = "system",
        expires_in_days: Optional[int] = None
    ) -> IPWhitelistEntry:
        """Add IP to whitelist."""
        entry_id = f"wl_{secrets.token_hex(8)}"
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=expires_in_days)
        
        entry = IPWhitelistEntry(
            id=entry_id,
            ip_address=ip_address,
            description=description,
            applies_to_endpoints=endpoints or [],
            added_by=added_by,
            added_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            expires_at=expires_at
        )
        
        self.whitelist[entry_id] = entry
        return entry
    
    def is_ip_whitelisted(
        self,
        ip_address: str,
        endpoint: Optional[str] = None
    ) -> bool:
        """Check if IP is whitelisted."""
        for entry in self.whitelist.values():
            if not entry.active:
                continue
            
            if entry.expires_at and datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) > entry.expires_at:
                continue
            
            # Simple IP match (in production use ipaddress.ip_address for CIDR)
            if entry.ip_address == ip_address:
                if endpoint is None or not entry.applies_to_endpoints:
                    return True
                if endpoint in entry.applies_to_endpoints:
                    return True
        
        return False
    
    def remove_from_whitelist(self, entry_id: str) -> bool:
        """Remove IP from whitelist."""
        if entry_id in self.whitelist:
            del self.whitelist[entry_id]
            return True
        
        return False

# ============= Geo-Blocking Manager =============

class GeoBlockingManager:
    """Manage geographic access restrictions."""
    
    def __init__(self):
        """Initialize geo-blocking manager."""
        self.rules: Dict[str, GeoBlockingRule] = {}
    
    def add_rule(
        self,
        rule_type: str,  # whitelist, blacklist
        countries: List[str],
        endpoints: List[str],
        operations: List[str] = None
    ) -> GeoBlockingRule:
        """Add geo-blocking rule."""
        rule_id = f"geo_{secrets.token_hex(8)}"
        
        rule = GeoBlockingRule(
            id=rule_id,
            rule_type=rule_type,
            countries=countries,
            applies_to_endpoints=endpoints,
            applies_to_operations=operations or [],
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
        
        self.rules[rule_id] = rule
        return rule
    
    def should_block(
        self,
        country_code: str,
        endpoint: str,
        operation: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if access should be blocked based on geography.
        Returns: (should_block, reason)
        """
        active_rules = [r for r in self.rules.values() if r.enabled]
        
        for rule in active_rules:
            # Check if rule applies to this endpoint
            if endpoint not in rule.applies_to_endpoints:
                continue
            
            # Check if rule applies to this operation
            if rule.applies_to_operations and operation not in rule.applies_to_operations:
                continue
            
            if rule.rule_type == "blacklist" and country_code in rule.countries:
                return True, f"Access denied from country: {country_code}"
            
            if rule.rule_type == "whitelist" and country_code not in rule.countries:
                return True, f"Access only allowed from whitelisted countries"
        
        return False, None

# ============= Security Headers Manager =============

class SecurityHeadersManager:
    """Manage security headers for API responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cache-Control": "no-store, no-cache, must-revalidate, private"
        }
