"""
LEATrace Confidence Engine Tests — Production.

Tests the weighted confidence scoring system.
"""

import datetime
import pytest
from app.confidence_engine import confidence_engine, ConfidenceEngine


class TestConfidenceComputation:
    """Tests confidence score computation."""

    def test_basic_computation(self):
        result = confidence_engine.compute_confidence(
            source_provider="OFAC_SDN",
            observation_count=5,
            unique_sources=2,
        )
        assert "confidence_score" in result
        assert 0 <= result["confidence_score"] <= 100
        assert "components" in result
        assert len(result["components"]) == 8

    def test_high_confidence_from_trusted_source(self):
        result = confidence_engine.compute_confidence(
            source_provider="MITRE_ATTACK",
            observation_count=20,
            unique_sources=4,
            false_positive_count=0,
            last_seen=datetime.datetime.utcnow(),
        )
        assert result["confidence_score"] >= 70

    def test_low_confidence_from_unknown_source(self):
        result = confidence_engine.compute_confidence(
            source_provider="unknown",
            observation_count=1,
            unique_sources=1,
            false_positive_count=2,
        )
        assert result["confidence_score"] < 50

    def test_age_decay(self):
        """Older IOCs should have lower confidence."""
        recent = confidence_engine.compute_confidence(
            source_provider="TAXII",
            last_seen=datetime.datetime.utcnow(),
        )
        old = confidence_engine.compute_confidence(
            source_provider="TAXII",
            last_seen=datetime.datetime.utcnow() - datetime.timedelta(days=180),
        )
        assert recent["confidence_score"] > old["confidence_score"]

    def test_false_positive_impact(self):
        """High FP count should lower confidence."""
        clean = confidence_engine.compute_confidence(
            source_provider="TAXII",
            observation_count=10,
            false_positive_count=0,
        )
        noisy = confidence_engine.compute_confidence(
            source_provider="TAXII",
            observation_count=10,
            false_positive_count=5,
        )
        assert clean["confidence_score"] > noisy["confidence_score"]

    def test_cross_feed_correlation_boost(self):
        """IOCs seen in multiple feeds should have higher confidence."""
        single = confidence_engine.compute_confidence(
            source_provider="TAXII",
            unique_sources=1,
        )
        multi = confidence_engine.compute_confidence(
            source_provider="TAXII",
            unique_sources=4,
        )
        assert multi["confidence_score"] > single["confidence_score"]

    def test_observation_frequency_boost(self):
        """More observations should increase confidence."""
        few = confidence_engine.compute_confidence(
            source_provider="TAXII",
            observation_count=1,
        )
        many = confidence_engine.compute_confidence(
            source_provider="TAXII",
            observation_count=100,
        )
        assert many["confidence_score"] > few["confidence_score"]


class TestConfidenceComponentBreakdown:
    """Tests that all components are present and documented."""

    def test_all_components_present(self):
        result = confidence_engine.compute_confidence()
        expected = {
            "source_reputation", "feed_quality", "observation_frequency",
            "age_freshness", "false_positive_rate", "cross_feed_correlation",
            "analyst_validation", "historical_accuracy",
        }
        assert set(result["components"].keys()) == expected

    def test_component_has_explanation(self):
        result = confidence_engine.compute_confidence()
        for name, component in result["components"].items():
            assert "score" in component, f"Component {name} missing score"
            assert "weight" in component, f"Component {name} missing weight"
            assert "explanation" in component, f"Component {name} missing explanation"


class TestConfidenceWeights:
    """Tests weight configuration."""

    def test_default_weights_sum_to_one(self):
        total = sum(confidence_engine.weights.values())
        assert abs(total - 1.0) < 0.01

    def test_custom_weights(self):
        engine = ConfidenceEngine(weights={
            "source_reputation": 0.5,
            "feed_quality": 0.1,
            "observation_frequency": 0.1,
            "age_freshness": 0.1,
            "false_positive_rate": 0.1,
            "cross_feed_correlation": 0.05,
            "analyst_validation": 0.025,
            "historical_accuracy": 0.025,
        })
        result = engine.compute_confidence(source_provider="MITRE_ATTACK")
        # MITRE_ATTACK has high reputation, and with 50% weight on reputation,
        # the score should be high
        assert result["confidence_score"] > 60
