"""
LEATrace IOC Confidence Engine — Production.

Computes transparent, explainable confidence scores for IOCs based on
multiple weighted factors.

PRODUCTION INVARIANTS:
- No hardcoded confidence values.
- Every score is computed from observable data.
- Score components are fully transparent and auditable.
- Recalculation on new observations.
"""

from __future__ import annotations

import datetime
import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger("leatrace.confidence_engine")

# Default component weights (configurable)
DEFAULT_WEIGHTS = {
    "source_reputation":     0.20,
    "feed_quality":          0.15,
    "observation_frequency": 0.15,
    "age_freshness":         0.10,
    "false_positive_rate":   0.15,
    "cross_feed_correlation": 0.15,
    "analyst_validation":    0.05,
    "historical_accuracy":   0.05,
}

# Known provider reputation scores (baseline, updated by history)
DEFAULT_PROVIDER_REPUTATION = {
    "OFAC_SDN":        95.0,
    "EU_CONSOLIDATED": 90.0,
    "MITRE_ATTACK":    98.0,
    "TAXII":           70.0,  # Depends on specific server
    "analyst":         85.0,
    "unknown":         30.0,
}


class ConfidenceEngine:
    """
    Transparent IOC confidence scoring engine.

    Computes confidence from 8 weighted factors:
    1. Source reputation: trust level of the provider
    2. Feed quality: false positive rate, update frequency
    3. Observation frequency: how many times the IOC was seen
    4. Age freshness: newer observations = higher confidence
    5. False positive rate: per-IOC FP tracking
    6. Cross-feed correlation: seen in multiple feeds
    7. Analyst validation: manual analyst input
    8. Historical accuracy: provider's historical true positive rate

    All components produce 0-100 sub-scores which are combined via
    configurable weights into a final 0-100 confidence score.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning("Confidence weights sum to %.2f, normalizing to 1.0", total)
            for k in self.weights:
                self.weights[k] /= total

    def compute_confidence(
        self,
        ioc_entry: Any = None,
        source_provider: Optional[str] = None,
        observation_count: int = 1,
        unique_sources: int = 1,
        false_positive_count: int = 0,
        first_seen: Optional[datetime.datetime] = None,
        last_seen: Optional[datetime.datetime] = None,
        analyst_score: Optional[float] = None,
        provider_accuracy: Optional[float] = None,
        feed_fp_rate: Optional[float] = None,
        feed_update_frequency_hours: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes a confidence score with full component breakdown.

        Args:
            ioc_entry: Optional IOCEntry ORM object (auto-extracts fields)
            source_provider: Provider name for reputation lookup
            observation_count: How many times this IOC was observed
            unique_sources: Number of distinct sources reporting this IOC
            false_positive_count: Number of FP reports for this IOC
            first_seen: When the IOC was first observed
            last_seen: When the IOC was last observed
            analyst_score: Manual analyst confidence (0-100)
            provider_accuracy: Historical true positive rate (0-100)
            feed_fp_rate: Feed's false positive rate (0.0-1.0)
            feed_update_frequency_hours: How often the feed updates

        Returns:
            Dict with final score and component breakdown
        """
        # Extract from IOC entry if provided
        if ioc_entry is not None:
            source_provider = source_provider or getattr(ioc_entry, "source_provider", None)
            observation_count = getattr(ioc_entry, "observation_count", observation_count)
            false_positive_count = getattr(ioc_entry, "false_positive_count", false_positive_count)
            first_seen = first_seen or getattr(ioc_entry, "first_seen", None)
            last_seen = last_seen or getattr(ioc_entry, "last_seen", None)

        now = datetime.datetime.utcnow()
        components: Dict[str, Dict[str, Any]] = {}

        # 1. Source Reputation (0-100)
        rep_score = DEFAULT_PROVIDER_REPUTATION.get(
            source_provider or "unknown",
            DEFAULT_PROVIDER_REPUTATION["unknown"],
        )
        components["source_reputation"] = {
            "score": rep_score,
            "weight": self.weights["source_reputation"],
            "provider": source_provider,
            "explanation": f"Provider '{source_provider}' has baseline reputation {rep_score}",
        }

        # 2. Feed Quality (0-100)
        fq_score = 50.0
        if feed_fp_rate is not None:
            fq_score = max(0.0, 100.0 - (feed_fp_rate * 200.0))
        if feed_update_frequency_hours is not None:
            # Bonus for frequently updated feeds
            if feed_update_frequency_hours <= 1:
                fq_score = min(100.0, fq_score + 20.0)
            elif feed_update_frequency_hours <= 24:
                fq_score = min(100.0, fq_score + 10.0)
        components["feed_quality"] = {
            "score": fq_score,
            "weight": self.weights["feed_quality"],
            "fp_rate": feed_fp_rate,
            "update_frequency_hours": feed_update_frequency_hours,
            "explanation": f"Feed quality score {fq_score:.1f}",
        }

        # 3. Observation Frequency (0-100)
        # Logarithmic scale: 1 obs=20, 5=50, 20=80, 100+=100
        obs_score = min(100.0, 20.0 + 17.0 * math.log2(max(1, observation_count)))
        components["observation_frequency"] = {
            "score": obs_score,
            "weight": self.weights["observation_frequency"],
            "count": observation_count,
            "explanation": f"Observed {observation_count} times → score {obs_score:.1f}",
        }

        # 4. Age Freshness (0-100)
        # Exponential decay: 100 at day 0, ~50 at 30 days, ~20 at 90 days
        age_score = 50.0
        if last_seen:
            age_days = max(0, (now - last_seen).days)
            age_score = max(5.0, 100.0 * math.exp(-0.023 * age_days))
        components["age_freshness"] = {
            "score": age_score,
            "weight": self.weights["age_freshness"],
            "last_seen": last_seen.isoformat() if last_seen else None,
            "explanation": f"Last seen age decay → score {age_score:.1f}",
        }

        # 5. False Positive Rate (0-100)
        # Higher FP count = lower score
        fp_ratio = false_positive_count / max(1, observation_count)
        fp_score = max(0.0, 100.0 - (fp_ratio * 200.0))
        components["false_positive_rate"] = {
            "score": fp_score,
            "weight": self.weights["false_positive_rate"],
            "fp_count": false_positive_count,
            "total_observations": observation_count,
            "fp_ratio": round(fp_ratio, 4),
            "explanation": f"FP ratio {fp_ratio:.2%} → score {fp_score:.1f}",
        }

        # 6. Cross-Feed Correlation (0-100)
        # Seen in multiple feeds = higher confidence
        corr_score = min(100.0, unique_sources * 25.0)
        components["cross_feed_correlation"] = {
            "score": corr_score,
            "weight": self.weights["cross_feed_correlation"],
            "unique_sources": unique_sources,
            "explanation": f"Reported by {unique_sources} unique sources → score {corr_score:.1f}",
        }

        # 7. Analyst Validation (0-100)
        av_score = analyst_score if analyst_score is not None else 50.0
        components["analyst_validation"] = {
            "score": av_score,
            "weight": self.weights["analyst_validation"],
            "analyst_provided": analyst_score is not None,
            "explanation": (
                f"Analyst set confidence to {av_score:.1f}"
                if analyst_score is not None
                else "No analyst validation — using neutral score 50"
            ),
        }

        # 8. Historical Accuracy (0-100)
        ha_score = provider_accuracy if provider_accuracy is not None else 50.0
        components["historical_accuracy"] = {
            "score": ha_score,
            "weight": self.weights["historical_accuracy"],
            "provider_accuracy": provider_accuracy,
            "explanation": (
                f"Provider historical accuracy: {ha_score:.1f}%"
                if provider_accuracy is not None
                else "No historical accuracy data — using neutral score 50"
            ),
        }

        # Compute weighted final score
        final_score = sum(
            components[k]["score"] * components[k]["weight"]
            for k in components
        )
        final_score = max(0.0, min(100.0, final_score))

        return {
            "confidence_score": round(final_score, 1),
            "components": components,
            "weights_used": dict(self.weights),
            "computed_at": now.isoformat(),
        }

    def recalculate_ioc_confidence(
        self,
        ioc_id: str,
        db: Any,
    ) -> Dict[str, Any]:
        """
        Recalculates confidence for an IOC from its current DB state.
        Updates the IOC's confidence_score in the database.
        """
        if db is None:
            return {"status": "db_unavailable"}

        from .stix_models import IOCEntry, IOCObservation

        try:
            entry = db.query(IOCEntry).filter(IOCEntry.id == ioc_id).first()
            if not entry:
                return {"status": "not_found", "ioc_id": ioc_id}

            # Count unique sources
            unique_sources = (
                db.query(IOCObservation.source_provider)
                .filter(
                    IOCObservation.ioc_id == ioc_id,
                    IOCObservation.source_provider.isnot(None),
                )
                .distinct()
                .count()
            )

            result = self.compute_confidence(
                ioc_entry=entry,
                unique_sources=max(1, unique_sources),
            )

            # Update the IOC
            entry.confidence_score = result["confidence_score"]
            entry.updated_at = datetime.datetime.utcnow()
            db.commit()

            result["ioc_id"] = ioc_id
            result["updated"] = True
            return result

        except Exception as e:
            logger.error("Confidence recalculation failed for %s: %s", ioc_id, e)
            return {"status": "error", "message": str(e)[:300]}

    def batch_recalculate(
        self,
        db: Any,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """Recalculates confidence for all active IOCs."""
        if db is None:
            return {"status": "db_unavailable"}

        from .stix_models import IOCEntry

        try:
            total = db.query(IOCEntry).filter(
                IOCEntry.status == "active"
            ).count()
            updated = 0
            offset = 0

            while offset < total:
                entries = (
                    db.query(IOCEntry)
                    .filter(IOCEntry.status == "active")
                    .offset(offset)
                    .limit(batch_size)
                    .all()
                )
                for entry in entries:
                    self.recalculate_ioc_confidence(entry.id, db)
                    updated += 1
                offset += batch_size

            return {
                "status": "completed",
                "total_processed": updated,
                "computed_at": datetime.datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Batch confidence recalculation failed: %s", e)
            return {"status": "error", "message": str(e)[:300]}


# ─── Singleton ────────────────────────────────────────────────────────────────

confidence_engine = ConfidenceEngine()
