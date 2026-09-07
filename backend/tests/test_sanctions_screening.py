"""
LEATrace Sanctions Screening Engine — Test Suite.

Tests the sanctions screening engine for:
- Wallet screening (hit/miss)
- Entity name screening (exact, alias, fuzzy)
- Transaction screening
- Batch screening
- Audit log creation
- Cache behavior
- Edge cases
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from app.sanctions_screening_engine import SanctionsScreeningEngine


class TestSanctionsScreeningWallet(unittest.TestCase):
    """Tests for wallet address screening."""

    def setUp(self):
        self.engine = SanctionsScreeningEngine()

    def test_empty_address_returns_no_match(self):
        db = MagicMock()
        result = self.engine.screen_wallet("", db, checked_by="test")
        self.assertFalse(result["matched"])
        self.assertEqual(result["query_type"], "wallet")

    def test_whitespace_address_returns_no_match(self):
        db = MagicMock()
        result = self.engine.screen_wallet("   ", db, checked_by="test")
        self.assertFalse(result["matched"])

    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._check_cache", return_value=None)
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._set_cache")
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._record_metric")
    def test_wallet_miss_returns_structured_result(self, mock_metric, mock_set_cache, mock_check_cache):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.first.return_value = None
        db.add = MagicMock()
        db.commit = MagicMock()

        result = self.engine.screen_wallet("0xdeadbeef", db, checked_by="test")

        self.assertFalse(result["matched"])
        self.assertEqual(result["query_value"], "0xdeadbeef")
        self.assertEqual(result["match_score"], 0.0)
        self.assertIn("screened_at", result)
        self.assertIn("response_time_ms", result)

    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._check_cache", return_value=None)
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._set_cache")
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._record_metric")
    def test_wallet_hit_returns_entity_details(self, mock_metric, mock_set_cache, mock_check_cache):
        db = MagicMock()

        # Mock wallet match
        mock_entity = MagicMock()
        mock_entity.id = "ent-1"
        mock_entity.name = "Lazarus Group"
        mock_entity.entity_type = "organization"
        mock_entity.program = "DPRK"
        mock_entity.provider_id = "ofac_sdn"
        mock_entity.remarks = "OFAC designated"
        mock_entity.status = "active"
        mock_entity.is_deleted = False

        mock_wallet = MagicMock()
        mock_wallet.entity = mock_entity
        mock_wallet.currency = "ETH"
        mock_wallet.normalized_address = "0xabc123"
        mock_wallet.is_deleted = False

        db.query.return_value.join.return_value.filter.return_value.first.return_value = mock_wallet
        db.add = MagicMock()
        db.commit = MagicMock()

        result = self.engine.screen_wallet("0xABC123", db, checked_by="test")

        self.assertTrue(result["matched"])
        self.assertEqual(result["match_score"], 1.0)
        self.assertEqual(result["entity_name"], "Lazarus Group")
        self.assertEqual(result["entity_type"], "organization")
        self.assertEqual(result["programs"], "DPRK")
        self.assertEqual(result["currency"], "ETH")

    def test_cached_result_returned_immediately(self):
        cached = {"matched": True, "entity_name": "Cached Entity"}
        with patch.object(self.engine, "_check_cache", return_value=cached):
            with patch.object(self.engine, "_record_metric") as mock_metric:
                db = MagicMock()
                result = self.engine.screen_wallet("0xfoo", db, checked_by="test")
                self.assertEqual(result, cached)
                mock_metric.assert_called_once_with(hit=True)


class TestSanctionsScreeningEntity(unittest.TestCase):
    """Tests for entity name screening."""

    def setUp(self):
        self.engine = SanctionsScreeningEngine()

    def test_empty_name_returns_no_match(self):
        db = MagicMock()
        result = self.engine.screen_entity("", db, checked_by="test")
        self.assertFalse(result["matched"])
        self.assertEqual(result["query_type"], "entity_name")

    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._check_cache", return_value=None)
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._set_cache")
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._record_metric")
    def test_exact_name_match(self, mock_metric, mock_set_cache, mock_check_cache):
        db = MagicMock()

        mock_entity = MagicMock()
        mock_entity.id = "ent-2"
        mock_entity.name = "Test Entity"
        mock_entity.entity_type = "individual"
        mock_entity.program = "IRAN"
        mock_entity.provider_id = "ofac_sdn"
        mock_entity.remarks = "Test"
        mock_entity.is_deleted = False

        db.query.return_value.filter.return_value.first.return_value = mock_entity
        db.add = MagicMock()
        db.commit = MagicMock()

        result = self.engine.screen_entity("Test Entity", db, checked_by="test")

        self.assertTrue(result["matched"])
        self.assertEqual(result["match_score"], 1.0)
        self.assertEqual(result["match_method"], "exact")

    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._check_cache", return_value=None)
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._set_cache")
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._record_metric")
    def test_no_match_returns_clean(self, mock_metric, mock_set_cache, mock_check_cache):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.join.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        db.query.return_value.join.return_value.filter.return_value.limit.return_value.all.return_value = []
        db.add = MagicMock()
        db.commit = MagicMock()

        result = self.engine.screen_entity("NonExistent Corp", db, checked_by="test")

        self.assertFalse(result["matched"])


class TestSanctionsScreeningTransaction(unittest.TestCase):
    """Tests for transaction screening (sender + receiver)."""

    def setUp(self):
        self.engine = SanctionsScreeningEngine()

    @patch.object(SanctionsScreeningEngine, "screen_wallet")
    def test_transaction_both_clean(self, mock_screen):
        mock_screen.return_value = {"matched": False, "match_score": 0, "entity_name": None, "programs": None}
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()

        result = self.engine.screen_transaction(
            "0xtxhash", "0xsender", "0xreceiver", db, checked_by="test",
        )
        self.assertFalse(result["matched"])
        self.assertFalse(result["sender"]["sanctioned"])
        self.assertFalse(result["receiver"]["sanctioned"])

    @patch.object(SanctionsScreeningEngine, "screen_wallet")
    def test_transaction_sender_sanctioned(self, mock_screen):
        def side_effect(addr, *args, **kwargs):
            if addr == "0xsender":
                return {"matched": True, "match_score": 1.0, "entity_name": "Bad Actor", "programs": "DPRK"}
            return {"matched": False, "match_score": 0, "entity_name": None, "programs": None}

        mock_screen.side_effect = side_effect
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()

        result = self.engine.screen_transaction(
            "0xtxhash", "0xsender", "0xreceiver", db, checked_by="test",
        )
        self.assertTrue(result["matched"])
        self.assertTrue(result["sender"]["sanctioned"])
        self.assertFalse(result["receiver"]["sanctioned"])


class TestSanctionsScreeningBatch(unittest.TestCase):
    """Tests for batch screening."""

    def setUp(self):
        self.engine = SanctionsScreeningEngine()

    def test_empty_batch_returns_no_results(self):
        db = MagicMock()
        result = self.engine.screen_batch([], db, checked_by="test")
        self.assertFalse(result["matched"])
        self.assertEqual(result["total"], 0)

    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._record_metric")
    def test_batch_with_no_matches(self, mock_metric):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        db.add = MagicMock()
        db.commit = MagicMock()

        result = self.engine.screen_batch(
            ["0xaaa", "0xbbb", "0xccc"], db, checked_by="test",
        )
        self.assertFalse(result["matched"])
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["hits"], 0)
        self.assertEqual(result["misses"], 3)


class TestNameSimilarity(unittest.TestCase):
    """Tests for the fuzzy name matching algorithm."""

    def setUp(self):
        self.engine = SanctionsScreeningEngine()

    def test_identical_names(self):
        score = self.engine._compute_name_similarity("john doe", "john doe")
        self.assertEqual(score, 1.0)

    def test_partial_overlap(self):
        score = self.engine._compute_name_similarity("john doe", "john smith")
        self.assertGreater(score, 0)
        self.assertLess(score, 1.0)

    def test_no_overlap(self):
        score = self.engine._compute_name_similarity("alice", "bob")
        self.assertEqual(score, 0.0)

    def test_empty_strings(self):
        score = self.engine._compute_name_similarity("", "test")
        self.assertEqual(score, 0.0)

    def test_case_insensitive(self):
        score = self.engine._compute_name_similarity("John Doe", "john doe")
        self.assertEqual(score, 1.0)


class TestAuditLogging(unittest.TestCase):
    """Tests that screening events produce audit logs."""

    def setUp(self):
        self.engine = SanctionsScreeningEngine()

    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._check_cache", return_value=None)
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._set_cache")
    @patch("app.sanctions_screening_engine.SanctionsScreeningEngine._record_metric")
    def test_screening_creates_audit_log(self, mock_metric, mock_set_cache, mock_check_cache):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.first.return_value = None

        self.engine.screen_wallet("0xtest", db, checked_by="inspector", reason_context="case-123")

        # Verify db.add was called (for the audit log)
        db.add.assert_called()
        db.commit.assert_called()


if __name__ == "__main__":
    unittest.main()
