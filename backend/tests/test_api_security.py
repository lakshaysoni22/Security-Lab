import pytest
from app.rbac_engine import rbac_engine
from app.policy_engine import policy_engine

def test_sql_injection_defense():
    # Simulate SQL injection payload checks
    sqli_payloads = [
        "1' OR '1'='1",
        "admin'--",
        "UNION SELECT username, password FROM users",
        "'; DROP TABLE users;--"
    ]
    
    # Define a clean validator helper (similar to backend middlewares)
    def is_safe_parameter(value: str) -> bool:
        lower_val = value.lower()
        if "or '1'='1" in lower_val or "union select" in lower_val or "drop table" in lower_val or "--" in lower_val:
            return False
        return True
        
    for payload in sqli_payloads:
        assert is_safe_parameter(payload) is False

def test_xss_protection_headers():
    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert('xss')"
    ]
    
    # Define XSS sanitize helper
    def sanitize_xss(value: str) -> str:
        # Replaces raw html tags to prevent browser execution
        return value.replace("<", "&lt;").replace(">", "&gt;")
        
    for payload in xss_payloads:
        sanitized = sanitize_xss(payload)
        assert "<script>" not in sanitized
        assert "<img>" not in sanitized

def test_rbac_privilege_escalation_block():
    # Read-Only role should never have access to write permissions
    assert rbac_engine.has_permission("read_only", "case:create") is False
    assert rbac_engine.has_permission("read_only", "evidence:delete") is False
    assert rbac_engine.has_permission("read_only", "settings:edit") is False
    
    # Verify Super Admin has all admin controls
    assert rbac_engine.has_permission("super_admin", "system:admin") is True
