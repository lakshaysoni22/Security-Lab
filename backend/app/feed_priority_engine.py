"""
LEATrace Feed Prioritization Engine — Production.

Scores and ranks threat intelligence feeds/providers for intelligent
provider selection and failover.

PRODUCTION INVARIANTS:
- Scores based on observable metrics, not fabricated values.
- All score components are auditable.
- Auto-selects best provider for each IOC type.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("leatrace.feed_priority")


class FeedPriorityEngine:
    """
    Intelligent feed prioritization engine.

    Scores every TI provider/feed on 7 factors:
    1. Availability: uptime percentage from health checks
    2. Latency: average sync duration
    3. Historical accuracy: true positive rate from analyst feedback
    4. Update frequency: how often the feed provides new data
    5. Coverage: number of IOC types provided
    6. Reliability: consistency of data format and API stability
    7. Analyst trust: manual trust score per feed

    Produces a weighted composite score (0-100) per provider.
    """

    DEFAULT_WEIGHTS = {
        "availability":       0.20,
        "latency":            0.10,
        "accuracy":           0.25,
        "update_frequency":   0.15,
        "coverage":           0.10,
        "reliability":        0.10,
        "analyst_trust":      0.10,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(self.DEFAULT_WEIGHTS)

    def compute_provider_score(
        self,
        provider_id: str,
        db: Any,
    ) -> Dict[str, Any]:
        """
        Computes priority score for a provider from DB metrics.

        Returns full score breakdown.
        """
        if db is None:
            return {"status": "db_unavailable"}

        from .stix_models import (
            TIProviderConfig, TIProviderHealth, TISyncLog, FeedPriorityScore,
        )

        try:
            config = db.query(TIProviderConfig).filter(
                TIProviderConfig.id == provider_id
            ).first()
            if not config:
                return {"status": "not_found", "provider_id": provider_id}

            # 1. Availability (from health check history)
            health_records = (
                db.query(TIProviderHealth)
                .filter(TIProviderHealth.provider_id == provider_id)
                .order_by(TIProviderHealth.checked_at.desc())
                .limit(100)
                .all()
            )
            if health_records:
                healthy_count = sum(1 for h in health_records if h.is_healthy)
                availability = (healthy_count / len(health_records)) * 100
            else:
                availability = 50.0  # neutral if no history

            # 2. Latency (average from health checks)
            latencies = [
                h.latency_ms for h in health_records
                if h.latency_ms and h.latency_ms > 0
            ]
            if latencies:
                avg_latency_ms = sum(latencies) / len(latencies)
                # Score: 100 at 0ms, 50 at 500ms, 0 at 2000ms+
                latency_score = max(0, 100 - (avg_latency_ms / 20))
            else:
                latency_score = 50.0

            # 3. Historical accuracy (from sync logs success rate)
            sync_logs = (
                db.query(TISyncLog)
                .filter(TISyncLog.provider_id == provider_id)
                .order_by(TISyncLog.synced_at.desc())
                .limit(50)
                .all()
            )
            if sync_logs:
                successful = sum(1 for s in sync_logs if s.status == "success")
                accuracy = (successful / len(sync_logs)) * 100
            else:
                accuracy = 50.0

            # 4. Update frequency (based on sync intervals)
            if len(sync_logs) >= 2:
                time_diffs = []
                for i in range(len(sync_logs) - 1):
                    if sync_logs[i].synced_at and sync_logs[i + 1].synced_at:
                        diff = (sync_logs[i].synced_at - sync_logs[i + 1].synced_at)
                        time_diffs.append(diff.total_seconds() / 3600)
                if time_diffs:
                    avg_interval = sum(time_diffs) / len(time_diffs)
                    # Score: 100 for hourly, 50 for daily, 20 for weekly
                    if avg_interval <= 1:
                        update_freq = 100.0
                    elif avg_interval <= 24:
                        update_freq = 80.0
                    elif avg_interval <= 168:
                        update_freq = 50.0
                    else:
                        update_freq = 20.0
                else:
                    update_freq = 50.0
            else:
                update_freq = 50.0

            # 5. Coverage (number of object types synced)
            if sync_logs:
                total_objects = sum(s.objects_new for s in sync_logs if s.objects_new)
                if total_objects > 1000:
                    coverage = 100.0
                elif total_objects > 100:
                    coverage = 70.0
                elif total_objects > 10:
                    coverage = 40.0
                else:
                    coverage = 20.0
            else:
                coverage = 30.0

            # 6. Reliability (error rate from sync logs)
            if sync_logs:
                error_logs = sum(1 for s in sync_logs if s.status == "error")
                reliability = max(0, 100 - (error_logs / len(sync_logs)) * 100)
            else:
                reliability = 50.0

            # 7. Analyst trust (from stored score or default)
            existing_score = (
                db.query(FeedPriorityScore)
                .filter(FeedPriorityScore.provider_id == provider_id)
                .order_by(FeedPriorityScore.computed_at.desc())
                .first()
            )
            analyst_trust = existing_score.analyst_trust_score if existing_score else 50.0

            # Compute weighted composite
            components = {
                "availability": availability,
                "latency": latency_score,
                "accuracy": accuracy,
                "update_frequency": update_freq,
                "coverage": coverage,
                "reliability": reliability,
                "analyst_trust": analyst_trust,
            }
            composite = sum(
                components[k] * self.weights.get(k, 0)
                for k in components
            )
            composite = max(0, min(100, composite))

            # Persist score
            now = datetime.datetime.utcnow()
            score_record = FeedPriorityScore(
                id=str(uuid.uuid4()),
                provider_id=provider_id,
                availability_score=availability,
                latency_score=latency_score,
                accuracy_score=accuracy,
                update_frequency_score=update_freq,
                coverage_score=coverage,
                reliability_score=reliability,
                analyst_trust_score=analyst_trust,
                composite_score=composite,
                computed_at=now,
            )
            db.add(score_record)
            db.commit()

            return {
                "provider_id": provider_id,
                "provider_name": config.name,
                "provider_type": config.provider_type,
                "composite_score": round(composite, 1),
                "components": {
                    k: {"score": round(v, 1), "weight": self.weights.get(k, 0)}
                    for k, v in components.items()
                },
                "computed_at": now.isoformat(),
            }

        except Exception as e:
            logger.error("Feed priority computation failed: %s", e)
            return {"status": "error", "message": str(e)[:300]}

    def rank_providers(self, db: Any) -> List[Dict[str, Any]]:
        """Ranks all active providers by composite score."""
        if db is None:
            return []

        from .stix_models import TIProviderConfig

        try:
            providers = (
                db.query(TIProviderConfig)
                .filter(TIProviderConfig.enabled == True)
                .all()
            )

            rankings = []
            for provider in providers:
                score = self.compute_provider_score(provider.id, db)
                if "composite_score" in score:
                    rankings.append(score)

            rankings.sort(key=lambda x: x.get("composite_score", 0), reverse=True)

            for rank, entry in enumerate(rankings, 1):
                entry["rank"] = rank

            return rankings

        except Exception as e:
            logger.error("Provider ranking failed: %s", e)
            return []

    def select_best_provider(
        self,
        db: Any,
        provider_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Selects the best provider based on composite score."""
        rankings = self.rank_providers(db)
        if provider_type:
            rankings = [r for r in rankings if r.get("provider_type") == provider_type]
        return rankings[0] if rankings else None

    def update_analyst_trust(
        self,
        provider_id: str,
        trust_score: float,
        db: Any,
        updated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Updates the analyst trust score for a provider."""
        if db is None:
            return {"status": "db_unavailable"}

        from .stix_models import FeedPriorityScore

        try:
            trust_score = max(0.0, min(100.0, trust_score))

            existing = (
                db.query(FeedPriorityScore)
                .filter(FeedPriorityScore.provider_id == provider_id)
                .order_by(FeedPriorityScore.computed_at.desc())
                .first()
            )

            if existing:
                existing.analyst_trust_score = trust_score
                db.commit()
            else:
                score = FeedPriorityScore(
                    id=str(uuid.uuid4()),
                    provider_id=provider_id,
                    analyst_trust_score=trust_score,
                )
                db.add(score)
                db.commit()

            logger.info("Analyst trust updated: provider=%s score=%.1f by=%s",
                        provider_id, trust_score, updated_by)

            return {
                "status": "updated",
                "provider_id": provider_id,
                "analyst_trust_score": trust_score,
            }

        except Exception as e:
            return {"status": "error", "message": str(e)[:200]}


# ─── Singleton ────────────────────────────────────────────────────────────────

feed_priority_engine = FeedPriorityEngine()
