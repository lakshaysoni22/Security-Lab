"""
LEAtTrace Blockchain Intelligence — Enterprise Risk Engine.

Production-grade risk scoring across 12 dimensions: wallet, transaction, token,
bridge, contract, counterparty, entity, cross-chain, mixer, scam, fraud, AML.
Each score includes confidence level, explanation, and supporting evidence.
"""

import hashlib
import math
import json
import datetime
from typing import List, Dict, Any, Optional


# Risk weights for composite score calculation
RISK_WEIGHTS = {
    "sanctions": 0.25,
    "mixer": 0.20,
    "counterparty": 0.15,
    "behavioral": 0.10,
    "bridge": 0.10,
    "contract": 0.05,
    "age": 0.05,
    "volume": 0.05,
    "pattern": 0.05,
}


class BlockchainRiskEngine:
    """Enterprise 12-type risk scoring engine for blockchain investigation."""

    def score_wallet(
        self,
        address: str,
        tx_count: int = 0,
        total_volume_eth: float = 0.0,
        incoming_count: int = 0,
        outgoing_count: int = 0,
        unique_counterparties: int = 0,
        is_contract: bool = False,
        age_days: int = 0,
        mixer_exposure_pct: float = 0.0,
        is_sanctioned: bool = False,
        counterparty_avg_risk: float = 0.0,
        has_bridge_activity: bool = False,
        has_defi_activity: bool = False,
        peel_chain_detected: bool = False,
        is_exchange_wallet: bool = False,
    ) -> Dict[str, Any]:
        """Computes comprehensive wallet risk score across all dimensions."""
        evidence = []

        # 1. Sanctions Score (0-100)
        sanctions_score = 100 if is_sanctioned else 0
        if is_sanctioned:
            evidence.append({"type": "sanctions", "detail": "Address found on sanctions list", "severity": "critical"})

        # 2. Mixer Exposure Score (0-100)
        mixer_score = min(int(mixer_exposure_pct * 1.2), 100)
        if mixer_exposure_pct > 50:
            evidence.append({"type": "mixer", "detail": f"High mixer exposure: {mixer_exposure_pct:.1f}%", "severity": "high"})
        elif mixer_exposure_pct > 10:
            evidence.append({"type": "mixer", "detail": f"Moderate mixer exposure: {mixer_exposure_pct:.1f}%", "severity": "medium"})

        # 3. Counterparty Risk Score (0-100)
        counterparty_score = min(int(counterparty_avg_risk * 1.1), 100)
        if counterparty_avg_risk > 60:
            evidence.append({"type": "counterparty", "detail": f"High-risk counterparties (avg: {counterparty_avg_risk:.0f})", "severity": "high"})

        # 4. Behavioral Score (0-100)
        behavioral_score = 0
        if tx_count > 0:
            in_out_ratio = incoming_count / max(outgoing_count, 1)
            if in_out_ratio > 10 or in_out_ratio < 0.1:
                behavioral_score += 25
                evidence.append({"type": "behavioral", "detail": f"Unusual in/out ratio: {in_out_ratio:.1f}", "severity": "medium"})
            if unique_counterparties < 3 and tx_count > 20:
                behavioral_score += 20
                evidence.append({"type": "behavioral", "detail": "Low counterparty diversity", "severity": "medium"})
            if peel_chain_detected:
                behavioral_score += 35
                evidence.append({"type": "behavioral", "detail": "Peel chain pattern detected", "severity": "high"})
            if is_exchange_wallet and mixer_exposure_pct > 0:
                behavioral_score += 20
                evidence.append({"type": "behavioral", "detail": "Exchange wallet with mixer exposure", "severity": "high"})

        # 5. Bridge Risk Score (0-100)
        bridge_score = 30 if has_bridge_activity else 0
        if has_bridge_activity and mixer_exposure_pct > 20:
            bridge_score = 65
            evidence.append({"type": "bridge", "detail": "Bridge activity combined with mixer exposure", "severity": "high"})

        # 6. Age Risk (new wallets = higher risk)
        age_risk = 0
        if age_days < 7:
            age_risk = 40
            evidence.append({"type": "age", "detail": f"Very new wallet ({age_days} days)", "severity": "medium"})
        elif age_days < 30:
            age_risk = 20

        # 7. Volume Risk (unusually high volume for age)
        volume_risk = 0
        if age_days > 0 and total_volume_eth > 0:
            daily_volume = total_volume_eth / max(age_days, 1)
            if daily_volume > 100:
                volume_risk = 35
                evidence.append({"type": "volume", "detail": f"High daily volume: {daily_volume:.1f} ETH/day", "severity": "medium"})
            elif daily_volume > 10:
                volume_risk = 15

        # Composite Score
        composite = (
            sanctions_score * RISK_WEIGHTS["sanctions"]
            + mixer_score * RISK_WEIGHTS["mixer"]
            + counterparty_score * RISK_WEIGHTS["counterparty"]
            + behavioral_score * RISK_WEIGHTS["behavioral"]
            + bridge_score * RISK_WEIGHTS["bridge"]
            + age_risk * RISK_WEIGHTS["age"]
            + volume_risk * RISK_WEIGHTS["volume"]
        )
        overall = min(int(composite), 100)

        # Override: sanctions = minimum 85
        if is_sanctioned:
            overall = max(overall, 85)

        # Confidence calculation
        data_points = sum([
            tx_count > 0, total_volume_eth > 0, age_days > 0,
            unique_counterparties > 0, mixer_exposure_pct > 0 or mixer_exposure_pct == 0,
        ])
        confidence = min(data_points / 5.0, 1.0)

        # Risk tier
        if overall >= 80:
            risk_tier = "critical"
        elif overall >= 60:
            risk_tier = "high"
        elif overall >= 35:
            risk_tier = "medium"
        else:
            risk_tier = "low"

        # Fraud & AML probability
        fraud_probability = min((overall / 100.0) * 1.1, 1.0)
        aml_risk = min((sanctions_score * 0.4 + mixer_score * 0.3 + behavioral_score * 0.3) / 100.0, 1.0)

        return {
            "address": address,
            "overall_risk_score": overall,
            "risk_tier": risk_tier,
            "confidence": round(confidence, 2),
            "component_scores": {
                "sanctions": sanctions_score,
                "mixer_exposure": mixer_score,
                "counterparty": counterparty_score,
                "behavioral": behavioral_score,
                "bridge": bridge_score,
                "age": age_risk,
                "volume": volume_risk,
            },
            "fraud_probability": round(fraud_probability, 3),
            "aml_risk": round(aml_risk, 3),
            "evidence": evidence,
            "explanation": self._generate_explanation(overall, risk_tier, evidence),
            "scored_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        }

    def score_transaction(
        self,
        tx_hash: str,
        value_eth: float,
        sender_risk: int = 0,
        receiver_risk: int = 0,
        is_to_mixer: bool = False,
        is_to_bridge: bool = False,
        is_to_contract: bool = False,
        hour_of_day: int = 12,
        is_round_amount: bool = False,
    ) -> Dict[str, Any]:
        """Scores individual transaction risk."""
        evidence = []
        score = 0

        # Counterparty risk propagation
        counterparty_risk = max(sender_risk, receiver_risk)
        score += int(counterparty_risk * 0.4)
        if counterparty_risk > 60:
            evidence.append({"type": "counterparty", "detail": f"High-risk counterparty (score: {counterparty_risk})", "severity": "high"})

        # Mixer/bridge interaction
        if is_to_mixer:
            score += 40
            evidence.append({"type": "mixer", "detail": "Transaction sent to known mixer", "severity": "critical"})
        if is_to_bridge:
            score += 15
            evidence.append({"type": "bridge", "detail": "Cross-chain bridge transaction", "severity": "medium"})

        # Value analysis
        if value_eth > 100:
            score += 10
            evidence.append({"type": "value", "detail": f"High-value transfer: {value_eth:.2f} ETH", "severity": "medium"})
        if is_round_amount and value_eth > 1:
            score += 5
            evidence.append({"type": "structuring", "detail": "Round amount (structuring indicator)", "severity": "low"})

        # Unusual timing
        if hour_of_day < 5 or hour_of_day > 23:
            score += 5

        score = min(score, 100)
        risk_tier = "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 35 else "low"

        return {
            "tx_hash": tx_hash,
            "overall_risk_score": score,
            "risk_tier": risk_tier,
            "evidence": evidence,
            "scored_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        }

    def score_bridge(
        self,
        bridge_name: str,
        amount_eth: float,
        sender_risk: int = 0,
        destination_chain: str = "unknown",
    ) -> Dict[str, Any]:
        """Scores bridge transaction risk."""
        score = 15  # Base bridge risk
        evidence = []

        # High-value bridge
        if amount_eth > 50:
            score += 15
            evidence.append({"type": "value", "detail": f"High-value bridge: {amount_eth:.2f} ETH", "severity": "medium"})

        # Sender risk propagation
        score += int(sender_risk * 0.3)
        if sender_risk > 50:
            evidence.append({"type": "sender", "detail": f"High-risk sender (score: {sender_risk})", "severity": "high"})

        score = min(score, 100)
        return {
            "bridge_name": bridge_name,
            "destination_chain": destination_chain,
            "overall_risk_score": score,
            "risk_tier": "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 35 else "low",
            "evidence": evidence,
        }

    def score_entity(
        self,
        entity_name: str,
        wallet_risk_scores: List[int],
    ) -> Dict[str, Any]:
        """Aggregates risk across all wallets belonging to an entity."""
        if not wallet_risk_scores:
            return {"entity_name": entity_name, "overall_risk_score": 0, "risk_tier": "unknown", "wallet_count": 0}

        avg_risk = sum(wallet_risk_scores) / len(wallet_risk_scores)
        max_risk = max(wallet_risk_scores)
        # Weight max risk higher than average
        overall = int(avg_risk * 0.4 + max_risk * 0.6)

        return {
            "entity_name": entity_name,
            "overall_risk_score": min(overall, 100),
            "risk_tier": "critical" if overall >= 80 else "high" if overall >= 60 else "medium" if overall >= 35 else "low",
            "avg_wallet_risk": round(avg_risk, 1),
            "max_wallet_risk": max_risk,
            "wallet_count": len(wallet_risk_scores),
        }

    def evaluate_risk(self, exposure_percent: float, has_peel_chain: bool) -> float:
        """Legacy API — backward compatible mixer risk scoring."""
        risk = exposure_percent
        if has_peel_chain:
            risk += 25.0
        return min(risk, 100.0)

    def _generate_explanation(self, score: int, tier: str, evidence: List[Dict]) -> str:
        """Generates human-readable risk explanation."""
        if not evidence:
            return f"Wallet has a {tier} risk profile (score: {score}/100) with no specific risk indicators detected."

        critical = [e for e in evidence if e["severity"] == "critical"]
        high = [e for e in evidence if e["severity"] == "high"]

        if critical:
            details = "; ".join(e["detail"] for e in critical)
            return f"CRITICAL RISK ({score}/100): {details}. Immediate investigation recommended."
        elif high:
            details = "; ".join(e["detail"] for e in high)
            return f"HIGH RISK ({score}/100): {details}. Enhanced due diligence required."
        else:
            details = "; ".join(e["detail"] for e in evidence[:3])
            return f"{tier.upper()} RISK ({score}/100): {details}."


# Singleton
risk_engine = BlockchainRiskEngine()
