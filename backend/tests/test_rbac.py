"""
LEATrace Unit Tests — RBAC & Security.

Tests for role hierarchy, permission checking, rate limiter,
and request sanitization.
"""

import pytest
from app.rbac import (
    ROLE_HIERARCHY,
    get_required_level,
    check_role_access,
    RateLimiter,
)


class TestRoleHierarchy:
    """Tests for role hierarchy levels."""

    def test_admin_highest(self):
        assert ROLE_HIERARCHY["admin"] == 100

    def test_readonly_lowest(self):
        assert ROLE_HIERARCHY["readonly"] == 10

    def test_hierarchy_order(self):
        assert ROLE_HIERARCHY["admin"] > ROLE_HIERARCHY["supervisor"]
        assert ROLE_HIERARCHY["supervisor"] > ROLE_HIERARCHY["investigator"]
        assert ROLE_HIERARCHY["investigator"] > ROLE_HIERARCHY["analyst"]
        assert ROLE_HIERARCHY["analyst"] > ROLE_HIERARCHY["auditor"]
        assert ROLE_HIERARCHY["auditor"] > ROLE_HIERARCHY["readonly"]


class TestPermissionChecking:
    """Tests for endpoint permission resolution."""

    def test_health_is_public(self):
        assert get_required_level("/api/health") == 0

    def test_auth_login_is_public(self):
        assert get_required_level("/api/auth/login") == 0

    def test_investigation_requires_investigator(self):
        level = get_required_level("/api/investigation/profile/0xabc")
        assert level >= 60

    def test_iam_requires_admin(self):
        level = get_required_level("/api/iam/users")
        assert level == 100

    def test_soc_requires_analyst(self):
        level = get_required_level("/api/soc/dashboard")
        assert level == 40

    def test_audit_requires_auditor(self):
        level = get_required_level("/api/audit/logs")
        assert level == 30


class TestRoleAccessCheck:
    """Tests for role access validation."""

    def test_admin_can_access_everything(self):
        assert check_role_access("admin", 100) is True
        assert check_role_access("admin", 60) is True
        assert check_role_access("admin", 0) is True

    def test_readonly_can_only_access_public(self):
        assert check_role_access("readonly", 0) is True
        assert check_role_access("readonly", 10) is True
        assert check_role_access("readonly", 60) is False

    def test_investigator_access(self):
        assert check_role_access("investigator", 60) is True
        assert check_role_access("investigator", 40) is True
        assert check_role_access("investigator", 80) is False

    def test_unknown_role_denied(self):
        assert check_role_access("unknown_role", 10) is False


class TestRateLimiter:
    """Tests for per-user rate limiting."""

    def test_allows_initial_requests(self):
        limiter = RateLimiter(requests_per_minute=5, requests_per_hour=100)
        assert limiter.is_allowed("user1") is True

    def test_blocks_after_limit(self):
        limiter = RateLimiter(requests_per_minute=3, requests_per_hour=100)
        for _ in range(3):
            assert limiter.is_allowed("user2") is True
            limiter.record_request("user2")
        assert limiter.is_allowed("user2") is False

    def test_different_users_independent(self):
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        for _ in range(2):
            limiter.record_request("userA")
        assert limiter.is_allowed("userA") is False
        assert limiter.is_allowed("userB") is True  # Different user

    def test_remaining_count(self):
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
        limiter.record_request("user3")
        limiter.record_request("user3")
        remaining = limiter.get_remaining("user3")
        assert remaining["rpm_remaining"] == 8
        assert remaining["rph_remaining"] == 98

    def test_hour_limit(self):
        limiter = RateLimiter(requests_per_minute=1000, requests_per_hour=5)
        for _ in range(5):
            limiter.record_request("user4")
        assert limiter.is_allowed("user4") is False
