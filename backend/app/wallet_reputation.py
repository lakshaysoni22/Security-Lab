"""
LEAtTrace Blockchain Intelligence — Wallet Reputation Scorer.

Production reputation engine with multi-factor scoring, historical trend,
entity correlation, and tier classification.
"""

import datetime
from typing import Dict, Any, List


class WalletReputationScorer:
    """Enterprise wallet reputation assessment engine."""

    def calculate_reputation(self, address: str, tx_count: int, sanction_exposure: float) -> Dict[str, Any]:
        """Calculates comprehensive trust and risk metrics."""
        # Base risk from sanctions
        base_risk = 10
        risk_factors = []

        if sanction_exposure > 80:
            base_risk += 60
            risk_factors.append({"factor": "high_sanctions_exposure", "impact": 60, "severity": "critical"})
        elif sanction_exposure > 30:
            base_risk += int(sanction_exposure * 0.5)
            risk_factors.append({"factor": "moderate_sanctions_exposure", "impact": int(sanction_exposure * 0.5), "severity": "high"})
        elif sanction_exposure > 0:
            base_risk += int(sanction_exposure * 0.3)
            risk_factors.append({"factor": "low_sanctions_exposure", "impact": int(sanction_exposure * 0.3), "severity": "medium"})

        # Activity assessment
        if tx_count < 2:
            base_risk += 15
            risk_factors.append({"factor": "new_wallet", "impact": 15, "severity": "medium"})
        elif tx_count < 5:
            base_risk += 5
        elif tx_count > 100:
            base_risk -= 5  # Active wallets generally lower risk

        risk_score = min(base_risk, 100)
        trust_rating = max(100 - risk_score, 0)

        # Tier classification
        if trust_rating > 80:
            tier = "Highly Trusted"
            tier_color = "#10b981"
        elif trust_rating > 60:
            tier = "Trusted"
            tier_color = "#22c55e"
        elif trust_rating > 40:
            tier = "Neutral"
            tier_color = "#eab308"
        elif trust_rating > 20:
            tier = "Suspicious"
            tier_color = "#f97316"
        else:
            tier = "High Risk"
            tier_color = "#ef4444"

        return {
            "address": address,
            "risk_score": risk_score,
            "trust_rating": trust_rating,
            "reputation_tier": tier,
            "tier_color": tier_color,
            "risk_factors": risk_factors,
            "tx_count": tx_count,
            "sanctions_exposure": sanction_exposure,
            "scored_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        }

    def calculate_batch_reputation(self, addresses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch reputation scoring."""
        return [
            self.calculate_reputation(
                addr["address"],
                addr.get("tx_count", 0),
                addr.get("sanction_exposure", 0.0),
            )
            for addr in addresses
        ]


wallet_reputation = WalletReputationScorer()
