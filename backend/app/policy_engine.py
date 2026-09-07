import time
from typing import Dict, Any

# Simple local state caches to avoid external DB dependencies
FAILED_LOGINS = {} # username -> { count, lock_until }
IP_BLACKLIST = {"198.51.100.42", "203.0.113.111"}
GEO_BLOCK_COUNTRIES = {"KP", "SY", "IR"}

class SecurityPolicyEngine:
    def verify_ip_access(self, ip_address: str, country_code: str = "IN") -> bool:
        """Enforces Geo-blocking and IP reputation blacklists."""
        if ip_address in IP_BLACKLIST:
            return False
        if country_code in GEO_BLOCK_COUNTRIES:
            return False
        return True

    def record_failed_login(self, username: str) -> None:
        """Records failed logins and triggers a lock if limits are exceeded."""
        now = time.time()
        record = FAILED_LOGINS.get(username, {"count": 0, "lock_until": 0.0})
        
        record["count"] += 1
        if record["count"] >= 5:
            record["lock_until"] = now + 600.0 # Lock for 10 minutes
            
        FAILED_LOGINS[username] = record

    def is_account_locked(self, username: str) -> bool:
        """Checks if account is locked out from brute-force attempts."""
        record = FAILED_LOGINS.get(username)
        if not record:
            return False
            
        now = time.time()
        if record["lock_until"] > now:
            return True
            
        # Lock expired, reset count
        if record["lock_until"] <= now and record["count"] >= 5:
            record["count"] = 0
            record["lock_until"] = 0.0
            FAILED_LOGINS[username] = record
            
        return False

    def reset_failed_logins(self, username: str) -> None:
        """Resets failed login counts on successful authentication."""
        if username in FAILED_LOGINS:
            FAILED_LOGINS[username] = {"count": 0, "lock_until": 0.0}

policy_engine = SecurityPolicyEngine()
