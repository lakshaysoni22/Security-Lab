"""
LEATrace Provider Manager Tests — Production.

Tests multi-provider registration, sync orchestration, failover, and health.
"""

import pytest
from unittest.mock import MagicMock
from app.threat_intel.provider_base import ThreatIntelProvider, ProviderStatus
from app.threat_intel.provider_manager import ProviderManager, ProviderRegistry


class MockProvider(ThreatIntelProvider):
    """Test provider that always succeeds."""

    def __init__(self, name="test", priority=50, configured=True, healthy=True):
        super().__init__(name=name, provider_type="test", priority=priority)
        self._configured = configured
        self._healthy = healthy
        if configured:
            self._status = ProviderStatus.ACTIVE

    def is_configured(self):
        return self._configured

    def sync(self, db, **kwargs):
        if not self._configured:
            return {"status": "not_configured"}
        return {
            "status": "success",
            "objects_fetched": 10,
            "objects_new": 5,
        }

    def health_check(self):
        return {
            "is_healthy": self._healthy,
            "latency_ms": 50.0,
        }


class FailingProvider(ThreatIntelProvider):
    """Test provider that always fails."""

    def __init__(self, name="failing", priority=50):
        super().__init__(name=name, provider_type="test", priority=priority)
        self._status = ProviderStatus.ACTIVE

    def is_configured(self):
        return True

    def sync(self, db, **kwargs):
        raise RuntimeError("Provider sync failed")

    def health_check(self):
        return {"is_healthy": False, "error": "Unreachable"}


class TestProviderRegistry:
    """Tests the provider registry."""

    def test_register_and_get(self):
        registry = ProviderRegistry()
        provider = MockProvider(name="test1")
        registry.register(provider)
        assert registry.get("test1") is provider

    def test_unregister(self):
        registry = ProviderRegistry()
        registry.register(MockProvider(name="test1"))
        registry.unregister("test1")
        assert registry.get("test1") is None

    def test_get_all(self):
        registry = ProviderRegistry()
        registry.register(MockProvider(name="a"))
        registry.register(MockProvider(name="b"))
        assert len(registry.get_all()) == 2

    def test_get_by_type(self):
        registry = ProviderRegistry()
        registry.register(MockProvider(name="a"))
        registry.register(MockProvider(name="b"))
        assert len(registry.get_by_type("test")) == 2
        assert len(registry.get_by_type("other")) == 0

    def test_get_active_excludes_unconfigured(self):
        registry = ProviderRegistry()
        registry.register(MockProvider(name="active", configured=True))
        registry.register(MockProvider(name="inactive", configured=False))
        active = registry.get_active()
        assert len(active) == 1
        assert active[0].name == "active"

    def test_get_sorted_by_priority(self):
        registry = ProviderRegistry()
        registry.register(MockProvider(name="low", priority=90))
        registry.register(MockProvider(name="high", priority=10))
        sorted_providers = registry.get_sorted_by_priority()
        assert sorted_providers[0].name == "high"
        assert sorted_providers[1].name == "low"


class TestProviderManager:
    """Tests the provider manager orchestration."""

    def test_sync_all(self):
        manager = ProviderManager()
        manager.register_provider(MockProvider(name="p1"))
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = manager.sync_all(mock_db)
        assert result["status"] == "completed"
        assert result["providers_synced"] == 1

    def test_sync_all_no_providers(self):
        manager = ProviderManager()
        result = manager.sync_all(MagicMock())
        assert result["status"] == "no_providers"

    def test_sync_all_no_db(self):
        manager = ProviderManager()
        result = manager.sync_all(None)
        assert result["status"] == "db_unavailable"

    def test_health_check_all(self):
        manager = ProviderManager()
        manager.register_provider(MockProvider(name="healthy", healthy=True))
        manager.register_provider(MockProvider(name="unhealthy", healthy=False))

        result = manager.health_check_all()
        assert result["total"] == 2
        assert result["healthy"] == 1

    def test_sync_with_failover(self):
        manager = ProviderManager()
        manager.register_provider(FailingProvider(name="primary", priority=10))
        manager.register_provider(MockProvider(name="backup", priority=20))

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = manager.sync_with_failover("test", mock_db)
        assert result["status"] == "success"

    def test_get_all_provider_status(self):
        manager = ProviderManager()
        manager.register_provider(MockProvider(name="p1"))
        statuses = manager.get_all_provider_status()
        assert len(statuses) == 1
        assert statuses[0]["name"] == "p1"

    def test_get_provider_health_not_found(self):
        manager = ProviderManager()
        result = manager.get_provider_health("nonexistent")
        assert result["status"] == "not_found"

    def test_sync_provider_not_found(self):
        manager = ProviderManager()
        result = manager.sync_provider("nonexistent", MagicMock())
        assert result["status"] == "not_found"


class TestProviderLifecycle:
    """Tests provider status lifecycle tracking."""

    def test_record_sync_success(self):
        provider = MockProvider(name="test")
        provider._record_sync_success(10, 5)
        assert provider._sync_count == 1
        assert provider._objects_synced == 5
        assert provider._status == ProviderStatus.ACTIVE

    def test_record_sync_error_degrades(self):
        provider = MockProvider(name="test")
        provider._record_sync_error("error 1")
        assert provider._status == ProviderStatus.DEGRADED
        provider._record_sync_error("error 2")
        assert provider._status == ProviderStatus.DEGRADED
        provider._record_sync_error("error 3")
        assert provider._status == ProviderStatus.FAILED

    def test_get_metrics(self):
        provider = MockProvider(name="test")
        provider._record_sync_success(10, 5)
        provider._record_sync_error("err")
        metrics = provider.get_metrics()
        assert metrics["sync_count"] == 1
        assert metrics["error_count"] == 1
        # error_rate = error_count / max(1, sync_count) * 100 = 1/1*100 = 100.0
        assert metrics["error_rate"] == 100.0
