"""
LEATrace Sanctions Provider Architecture — Test Suite.

Tests the provider base class, provider manager, registry,
and individual provider implementations.
"""

import unittest
from unittest.mock import MagicMock, patch
import time

from app.providers.sanctions_provider_base import SanctionsProvider, SanctionsProviderStatus
from app.providers.sanctions_provider_manager import (
    SanctionsProviderManager, SanctionsProviderRegistry,
)


class MockProvider(SanctionsProvider):
    """Test-only mock provider for unit tests."""

    def __init__(self, provider_id="mock", name="Mock", priority=50, configured=True,
                 parse_result=None, should_fail=False, fail_count=0):
        super().__init__(
            provider_id=provider_id,
            name=name,
            priority=priority,
            max_retries=2,
            backoff_factor=1.0,
            initial_backoff_seconds=0.01,
            max_backoff_seconds=0.1,
            requests_per_minute=100,
        )
        self._configured = configured
        self._parse_result = parse_result or {
            "checksum": "a" * 64,
            "entities": [{"entity_uid": "1", "name": "Test", "wallets": []}],
        }
        self._should_fail = should_fail
        self._fail_count = fail_count
        self._call_count = 0

    def is_configured(self) -> bool:
        return self._configured

    def _download_and_parse_impl(self):
        self._call_count += 1
        if self._should_fail:
            if self._fail_count == 0 or self._call_count <= self._fail_count:
                raise ConnectionError(f"Simulated failure #{self._call_count}")
        return self._parse_result

    def health_check(self):
        return {"is_healthy": self._configured, "provider_id": self.provider_id}


class TestSanctionsProviderBase(unittest.TestCase):
    """Tests for the SanctionsProvider abstract base class."""

    def test_initial_status_is_not_configured(self):
        p = MockProvider()
        self.assertEqual(p._status, SanctionsProviderStatus.NOT_CONFIGURED)

    def test_successful_download_updates_status(self):
        p = MockProvider()
        result = p.download_and_parse()
        self.assertEqual(p._status, SanctionsProviderStatus.ACTIVE)
        self.assertEqual(p._consecutive_failures, 0)
        self.assertIn("checksum", result)
        self.assertIn("entities", result)
        self.assertIn("attempts", result)
        self.assertEqual(result["attempts"], 1)

    def test_retry_on_failure(self):
        # Fails on first call, succeeds on second
        p = MockProvider(should_fail=True, fail_count=1)
        result = p.download_and_parse()
        self.assertEqual(p._call_count, 2)
        self.assertEqual(p._status, SanctionsProviderStatus.ACTIVE)

    def test_all_retries_exhausted_raises(self):
        p = MockProvider(should_fail=True, fail_count=99)
        with self.assertRaises(ConnectionError):
            p.download_and_parse()
        self.assertEqual(p._call_count, 2)  # max_retries=2
        self.assertIn(p._status, (SanctionsProviderStatus.DEGRADED, SanctionsProviderStatus.FAILED))

    def test_disabled_provider_raises(self):
        p = MockProvider()
        p.set_enabled(False)
        with self.assertRaises(RuntimeError):
            p.download_and_parse()

    def test_not_configured_provider_raises(self):
        p = MockProvider(configured=False)
        with self.assertRaises(RuntimeError):
            p.download_and_parse()

    def test_enable_disable_toggle(self):
        p = MockProvider()
        p.set_enabled(False)
        self.assertFalse(p.enabled)
        self.assertEqual(p._status, SanctionsProviderStatus.DISABLED)
        p.set_enabled(True)
        self.assertTrue(p.enabled)

    def test_get_status_returns_structured_dict(self):
        p = MockProvider()
        status = p.get_status()
        self.assertIn("provider_id", status)
        self.assertIn("name", status)
        self.assertIn("priority", status)
        self.assertIn("enabled", status)
        self.assertIn("status", status)
        self.assertIn("retry_config", status)
        self.assertIn("rate_limit", status)

    def test_integrity_validation_valid(self):
        p = MockProvider()
        result = {
            "checksum": "a" * 64,
            "entities": [
                {"entity_uid": "1", "name": "Test Entity", "wallets": []},
                {"entity_uid": "2", "name": "Another Entity", "wallets": [{"addr": "0x1"}]},
            ],
        }
        integrity = p.validate_integrity(result)
        self.assertTrue(integrity["valid"])
        self.assertEqual(integrity["total_entities"], 2)
        self.assertEqual(integrity["duplicate_uids"], 0)

    def test_integrity_validation_duplicate_uids(self):
        p = MockProvider()
        result = {
            "checksum": "a" * 64,
            "entities": [
                {"entity_uid": "1", "name": "Dup1", "wallets": []},
                {"entity_uid": "1", "name": "Dup2", "wallets": []},
            ],
        }
        integrity = p.validate_integrity(result)
        self.assertFalse(integrity["valid"])
        self.assertEqual(integrity["duplicate_uids"], 1)

    def test_integrity_validation_missing_checksum(self):
        p = MockProvider()
        result = {"checksum": "", "entities": []}
        integrity = p.validate_integrity(result)
        self.assertFalse(integrity["valid"])
        self.assertIn("Missing checksum", integrity["issues"])

    def test_sync_stats_recording(self):
        p = MockProvider()
        p._record_sync_stats(100, 50, 5.0)
        self.assertEqual(p._total_entities_synced, 100)
        self.assertEqual(p._total_wallets_synced, 50)
        self.assertEqual(p._avg_sync_duration_seconds, 5.0)

    def test_consecutive_failures_escalate_to_failed(self):
        p = MockProvider()
        p._record_failure("error 1")
        self.assertEqual(p._status, SanctionsProviderStatus.DEGRADED)
        p._record_failure("error 2")
        self.assertEqual(p._status, SanctionsProviderStatus.DEGRADED)
        p._record_failure("error 3")
        self.assertEqual(p._status, SanctionsProviderStatus.FAILED)


class TestSanctionsProviderRegistry(unittest.TestCase):
    """Tests for the provider registry."""

    def test_register_and_retrieve(self):
        registry = SanctionsProviderRegistry()
        p = MockProvider(provider_id="test1")
        registry.register(p)
        self.assertEqual(registry.get("test1"), p)

    def test_unregister(self):
        registry = SanctionsProviderRegistry()
        registry.register(MockProvider(provider_id="test1"))
        self.assertTrue(registry.unregister("test1"))
        self.assertIsNone(registry.get("test1"))

    def test_get_all(self):
        registry = SanctionsProviderRegistry()
        registry.register(MockProvider(provider_id="a"))
        registry.register(MockProvider(provider_id="b"))
        self.assertEqual(len(registry.get_all()), 2)

    def test_sorted_by_priority(self):
        registry = SanctionsProviderRegistry()
        registry.register(MockProvider(provider_id="low", priority=90))
        registry.register(MockProvider(provider_id="high", priority=10))
        sorted_providers = registry.get_sorted_by_priority()
        self.assertEqual(sorted_providers[0].provider_id, "high")
        self.assertEqual(sorted_providers[1].provider_id, "low")

    def test_disabled_excluded_from_sorted(self):
        registry = SanctionsProviderRegistry()
        p1 = MockProvider(provider_id="enabled", priority=10)
        p2 = MockProvider(provider_id="disabled", priority=5)
        p2.set_enabled(False)
        registry.register(p1)
        registry.register(p2)
        active = registry.get_sorted_by_priority()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].provider_id, "enabled")

    def test_unconfigured_excluded_from_sorted(self):
        registry = SanctionsProviderRegistry()
        p = MockProvider(provider_id="unconfig", configured=False)
        registry.register(p)
        self.assertEqual(len(registry.get_sorted_by_priority()), 0)


class TestSanctionsProviderManager(unittest.TestCase):
    """Tests for the provider manager orchestrator."""

    def test_default_providers_registered(self):
        manager = SanctionsProviderManager()
        all_providers = manager.registry.get_all()
        provider_ids = {p.provider_id for p in all_providers}
        self.assertIn("ofac_sdn", provider_ids)
        self.assertIn("eu_consolidated", provider_ids)
        self.assertIn("un_consolidated", provider_ids)

    def test_get_all_statuses(self):
        manager = SanctionsProviderManager()
        statuses = manager.get_all_statuses()
        self.assertIn("providers", statuses)
        self.assertIn("active_count", statuses)
        self.assertIn("total_count", statuses)
        self.assertGreater(statuses["total_count"], 0)

    def test_toggle_provider(self):
        manager = SanctionsProviderManager()
        result = manager.toggle_provider("ofac_sdn", False)
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["enabled"])
        # Re-enable
        result = manager.toggle_provider("ofac_sdn", True)
        self.assertTrue(result["enabled"])

    def test_toggle_nonexistent_provider(self):
        manager = SanctionsProviderManager()
        result = manager.toggle_provider("nonexistent", True)
        self.assertEqual(result["status"], "not_found")

    def test_sync_nonexistent_provider(self):
        manager = SanctionsProviderManager()
        db = MagicMock()
        result = manager.sync_provider("nonexistent", db)
        self.assertEqual(result["status"], "not_found")

    def test_health_check_all(self):
        manager = SanctionsProviderManager()
        # Health checks will fail (no network), but should return structured results
        results = manager.health_check_all()
        self.assertIn("total_providers", results)
        self.assertIn("providers", results)


if __name__ == "__main__":
    unittest.main()
