"""
LEATrace Unit Tests — Risk Engine & AML.

Tests for risk scoring, laundering detection, and AML analysis.
"""

import pytest
from app.risk_engine import BlockchainRiskEngine
from app.laundering_engine import LaunderingDetectionEngine


class TestWalletRiskScoring:
    """Tests for wallet risk scoring."""

    def setup_method(self):
        self.engine = BlockchainRiskEngine()

    def test_clean_wallet_low_risk(self):
        result = self.engine.score_wallet(
            address="0x1234567890abcdef1234567890abcdef12345678",
            tx_count=50,
            total_volume_eth=10.0,
            incoming_count=25,
            outgoing_count=25,
            unique_counterparties=15,
            age_days=365,
        )
        assert result["risk_tier"] == "low"
        assert result["overall_risk_score"] < 35

    def test_sanctioned_wallet_critical(self):
        result = self.engine.score_wallet(
            address="0x1234567890abcdef1234567890abcdef12345678",
            is_sanctioned=True,
        )
        assert result["risk_tier"] == "critical"
        assert result["overall_risk_score"] >= 85

    def test_high_mixer_exposure(self):
        result = self.engine.score_wallet(
            address="0x1234567890abcdef1234567890abcdef12345678",
            tx_count=100,
            mixer_exposure_pct=80.0,
        )
        assert result["overall_risk_score"] > 15
        assert any(e["type"] == "mixer" for e in result["evidence"])

    def test_peel_chain_detection(self):
        result = self.engine.score_wallet(
            address="0x1234567890abcdef1234567890abcdef12345678",
            tx_count=50,
            peel_chain_detected=True,
        )
        assert any(e["type"] == "behavioral" for e in result["evidence"])
        assert any("Peel chain" in e["detail"] for e in result["evidence"])

    def test_new_wallet_age_risk(self):
        result = self.engine.score_wallet(
            address="0x1234567890abcdef1234567890abcdef12345678",
            age_days=3,
            tx_count=10,
        )
        assert any(e["type"] == "age" for e in result["evidence"])

    def test_result_structure(self):
        result = self.engine.score_wallet(address="0x1234567890abcdef1234567890abcdef12345678")
        assert "overall_risk_score" in result
        assert "risk_tier" in result
        assert "confidence" in result
        assert "component_scores" in result
        assert "evidence" in result
        assert "explanation" in result
        assert "scored_at" in result
        assert 0 <= result["overall_risk_score"] <= 100
        assert result["risk_tier"] in {"low", "medium", "high", "critical"}

    def test_risk_tiers(self):
        # Critical
        r = self.engine.score_wallet(address="0x0", is_sanctioned=True)
        assert r["risk_tier"] == "critical"

    def test_confidence_increases_with_data(self):
        r1 = self.engine.score_wallet(address="0x0")
        r2 = self.engine.score_wallet(address="0x0", tx_count=100, total_volume_eth=50, age_days=30, unique_counterparties=20)
        assert r2["confidence"] >= r1["confidence"]


class TestTransactionRiskScoring:
    """Tests for transaction risk scoring."""

    def setup_method(self):
        self.engine = BlockchainRiskEngine()

    def test_clean_transaction(self):
        result = self.engine.score_transaction(tx_hash="0x" + "a" * 64, value_eth=0.5)
        assert result["risk_tier"] == "low"

    def test_mixer_transaction(self):
        result = self.engine.score_transaction(tx_hash="0x" + "a" * 64, value_eth=10.0, is_to_mixer=True)
        assert result["overall_risk_score"] >= 40
        assert any(e["type"] == "mixer" for e in result["evidence"])

    def test_high_risk_counterparty(self):
        result = self.engine.score_transaction(tx_hash="0x" + "a" * 64, value_eth=1.0, sender_risk=90)
        assert result["overall_risk_score"] > 0
        assert any(e["type"] == "counterparty" for e in result["evidence"])


class TestEntityRiskScoring:
    """Tests for entity risk aggregation."""

    def setup_method(self):
        self.engine = BlockchainRiskEngine()

    def test_empty_entity(self):
        result = self.engine.score_entity("Test Entity", [])
        assert result["risk_tier"] == "unknown"

    def test_entity_aggregation(self):
        result = self.engine.score_entity("Test Entity", [10, 20, 30])
        assert result["wallet_count"] == 3
        assert result["avg_wallet_risk"] == 20.0
        assert result["max_wallet_risk"] == 30

    def test_high_risk_entity(self):
        result = self.engine.score_entity("Criminal Entity", [90, 85, 95])
        assert result["risk_tier"] in {"critical", "high"}


class TestPeelChainDetection:
    """Tests for peel chain detection."""

    def setup_method(self):
        self.engine = LaunderingDetectionEngine()

    def test_no_peel_chain(self):
        txs = [
            {"from": "0xaaa", "to": "0xbbb", "value": 5.0, "hash": "0x1"},
            {"from": "0xaaa", "to": "0xccc", "value": 5.0, "hash": "0x2"},
        ]
        result = self.engine.detect_peel_chain(txs, "0xaaa")
        assert result["is_peel_chain_active"] is False

    def test_peel_chain_detected(self):
        txs = [
            {"from": "0xaaa", "to": "0xb1", "value": 50.0, "hash": "0x1", "timestamp": "2024-01-01"},
            {"from": "0xaaa", "to": "0xb2", "value": 40.0, "hash": "0x2", "timestamp": "2024-01-02"},
            {"from": "0xaaa", "to": "0xb3", "value": 30.0, "hash": "0x3", "timestamp": "2024-01-03"},
            {"from": "0xaaa", "to": "0xb4", "value": 20.0, "hash": "0x4", "timestamp": "2024-01-04"},
            {"from": "0xaaa", "to": "0xb5", "value": 10.0, "hash": "0x5", "timestamp": "2024-01-05"},
        ]
        result = self.engine.detect_peel_chain(txs, "0xaaa")
        assert result["is_peel_chain_active"] is True
        assert result["detected_hops"] >= 3


class TestSmurfingDetection:
    """Tests for structuring/smurfing detection."""

    def setup_method(self):
        self.engine = LaunderingDetectionEngine()

    def test_no_structuring(self):
        txs = [
            {"from": "0xaaa", "to": "0xbbb", "value": 7.0, "hash": "0x1"},
        ]
        result = self.engine.detect_smurfing_pattern(txs, "0xaaa")
        assert result["is_structuring_detected"] is False

    def test_structuring_detected(self):
        # Values just below round thresholds (smurfing pattern)
        txs = [
            {"from": "0xaaa", "to": "0xb1", "value": 0.95, "hash": "0x1"},
            {"from": "0xaaa", "to": "0xb2", "value": 0.92, "hash": "0x2"},
            {"from": "0xaaa", "to": "0xb3", "value": 0.88, "hash": "0x3"},
            {"from": "0xaaa", "to": "0xb4", "value": 0.97, "hash": "0x4"},
        ]
        result = self.engine.detect_smurfing_pattern(txs, "0xaaa")
        assert result["is_structuring_detected"] is True


class TestFullAMLAnalysis:
    """Tests for composite AML analysis."""

    def setup_method(self):
        self.engine = LaunderingDetectionEngine()

    def test_clean_address(self):
        txs = [
            {"from": "0xaaa", "to": "0xbbb", "value": 5.0, "hash": "0x1"},
        ]
        result = self.engine.full_aml_analysis(txs, "0xaaa")
        assert result["aml_risk_score"] == 0
        assert result["patterns_detected"] == 0
        assert result["risk_level"] == "low"

    def test_result_structure(self):
        result = self.engine.full_aml_analysis([], "0xaaa")
        assert "aml_risk_score" in result
        assert "patterns_detected" in result
        assert "peel_chain" in result
        assert "structuring" in result
        assert "layering" in result
        assert "round_amounts" in result
