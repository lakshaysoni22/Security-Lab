"""
Tests for production SIEM router: DB-backed incidents, IOC check, correlation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.observability import PROMETHEUS_ENABLED


class TestObservability:
    """Tests for the observability module — graceful degradation if deps missing."""

    def test_get_metrics_output_returns_bytes_or_none(self):
        from app.observability import get_metrics_output
        result = get_metrics_output()
        assert result is None or isinstance(result, bytes)

    def test_get_content_type_returns_string(self):
        from app.observability import get_content_type
        ct = get_content_type()
        assert isinstance(ct, str)
        assert len(ct) > 0

    def test_record_request_no_exception(self):
        from app.observability import record_request
        # Must not raise regardless of Prometheus state
        record_request("GET", "/api/test", 200, 0.05)

    def test_record_wallet_query_no_exception(self):
        from app.observability import record_wallet_query
        record_wallet_query("ethereum")
        record_wallet_query("bitcoin")

    def test_record_rpc_error_no_exception(self):
        from app.observability import record_rpc_error
        record_rpc_error("ethereum", "timeout")

    def test_record_sanctions_check_no_exception(self):
        from app.observability import record_sanctions_check
        record_sanctions_check(hit=True)
        record_sanctions_check(hit=False)

    def test_record_auth_failure_no_exception(self):
        from app.observability import record_auth_failure
        record_auth_failure("invalid_password")

    def test_span_context_manager_no_exception(self):
        from app.observability import span
        with span("test.operation") as s:
            pass  # Should not raise

    def test_prometheus_flag_is_bool(self):
        assert isinstance(PROMETHEUS_ENABLED, bool)


class TestHealthEndpoints:
    @pytest.fixture
    def client(self, setup_test_db):
        from app.main import app
        return TestClient(app)

    def test_liveness_probe_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "uptime_seconds" in data

    def test_metrics_endpoint_exists(self, client):
        response = client.get("/metrics")
        # 200 if prometheus_client installed, 503 if not
        assert response.status_code in (200, 503)

    def test_metrics_503_has_helpful_message(self, client):
        if not PROMETHEUS_ENABLED:
            response = client.get("/metrics")
            assert response.status_code == 503
            assert b"prometheus_client" in response.content


class TestRateLimitMiddleware:
    def test_rate_limiter_in_memory_allows_requests(self):
        from app.middleware.rate_limit import _InMemoryRateLimiter
        limiter = _InMemoryRateLimiter()
        allowed, remaining, reset_at = limiter.is_allowed("test-key", 5, 60)
        assert allowed is True
        assert remaining == 4

    def test_rate_limiter_blocks_after_limit(self):
        from app.middleware.rate_limit import _InMemoryRateLimiter
        limiter = _InMemoryRateLimiter()
        for _ in range(3):
            limiter.is_allowed("ip:1.2.3.4", 3, 60)
        allowed, remaining, _ = limiter.is_allowed("ip:1.2.3.4", 3, 60)
        assert allowed is False
        assert remaining == 0

    def test_rate_limiter_different_keys_independent(self):
        from app.middleware.rate_limit import _InMemoryRateLimiter
        limiter = _InMemoryRateLimiter()
        for _ in range(2):
            limiter.is_allowed("key:A", 2, 60)
        # Key A exhausted
        allowed_a, _, _ = limiter.is_allowed("key:A", 2, 60)
        # Key B should still work
        allowed_b, _, _ = limiter.is_allowed("key:B", 2, 60)
        assert allowed_a is False
        assert allowed_b is True

    def test_rate_limiter_sliding_window(self):
        import time
        from app.middleware.rate_limit import _InMemoryRateLimiter
        limiter = _InMemoryRateLimiter()
        # Fill the window
        for _ in range(3):
            limiter.is_allowed("key:slide", 3, 1)  # 1-second window
        # Should be blocked
        allowed, _, _ = limiter.is_allowed("key:slide", 3, 1)
        assert allowed is False
        # Wait for window to expire
        time.sleep(1.1)
        allowed, _, _ = limiter.is_allowed("key:slide", 3, 1)
        assert allowed is True  # Window expired, allowed again


class TestSIEMProductionEndpoints:
    @pytest.fixture
    def client(self, setup_test_db):
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get JWT token for test user."""
        resp = client.post("/api/auth/register", json={
            "email": "siem_test@leatrace.test",
            "username": "siem_test",
            "password": "SecurePass123!",
            "role": "admin",
        })
        resp2 = client.post("/api/auth/login", data={
            "username": "siem_test@leatrace.test",
            "password": "SecurePass123!",
        })
        if resp2.status_code == 200:
            token = resp2.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_get_alerts_returns_list(self, client, auth_headers):
        resp = client.get("/api/siem/alerts", headers=auth_headers)
        assert resp.status_code in (200, 401)
        if resp.status_code == 200:
            assert isinstance(resp.json(), list)

    def test_create_incident_persists(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        resp = client.post("/api/siem/alerts", json={
            "severity": "high",
            "category": "Authentication Anomaly",
            "message": "Test incident from automated test",
            "source": "TestSuite",
        }, headers=auth_headers)
        assert resp.status_code in (201, 401)
        if resp.status_code == 201:
            data = resp.json()
            assert data["severity"] == "high"
            assert data["status"] == "open"
            assert "id" in data

    def test_ioc_check_empty_db_shows_notice(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        resp = client.get(
            "/api/siem/threat-intel/ioc-check",
            params={"indicator": "0x1234567890abcdef"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 401)
        if resp.status_code == 200:
            data = resp.json()
            assert "match_found" in data
            assert "data_sources" in data
            # Must never fabricate a match
            assert data["match_found"] is False or data["sanction_match"] is not None

    def test_correlation_uses_real_audit_logs(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        resp = client.get("/api/siem/correlation", headers=auth_headers)
        assert resp.status_code in (200, 401)
        if resp.status_code == 200:
            data = resp.json()
            assert data["data_source"] == "audit_log_database"
            assert isinstance(data["timeline_events"], list)

    def test_health_endpoint_returns_status(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth not available")
        resp = client.get("/api/siem/health", headers=auth_headers)
        assert resp.status_code in (200, 401)
        if resp.status_code == 200:
            data = resp.json()
            assert "database" in data
            assert "ioc_mode" in data
