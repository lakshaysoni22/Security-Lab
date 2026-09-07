"""
LEAtTrace AI Platform — Feature Store.

Extracts and normalizes ML feature vectors from raw database entities
(wallets, transactions, cases, evidence) for model training and inference.
"""

import datetime
import math
from typing import List, Dict, Any, Optional


class FeatureStore:
    """Centralized feature extraction for all ML models."""

    # --- Wallet Features ---
    @staticmethod
    def extract_wallet_features(
        tx_count: int,
        total_value_eth: float,
        incoming_count: int,
        outgoing_count: int,
        unique_counterparties: int,
        is_contract: bool,
        age_days: int,
        mixer_exposure_pct: float,
        is_sanctioned: bool,
        risk_score: int,
        avg_tx_value: float = 0.0,
        max_tx_value: float = 0.0,
        tx_velocity_per_day: float = 0.0,
        has_token_transfers: bool = False,
    ) -> List[float]:
        """
        Produces a normalized 14-dimensional feature vector for wallet-level models.

        Features:
            0: log_tx_count           — log(1 + tx_count)
            1: log_total_value        — log(1 + total_value_eth)
            2: in_out_ratio           — incoming / (incoming + outgoing), or 0.5
            3: unique_party_ratio     — unique_counterparties / max(tx_count, 1)
            4: is_contract            — 1.0 / 0.0
            5: log_age_days           — log(1 + age_days)
            6: mixer_exposure_norm    — mixer_exposure_pct / 100.0
            7: is_sanctioned          — 1.0 / 0.0
            8: risk_score_norm        — risk_score / 100.0
            9: log_avg_tx_value       — log(1 + avg_tx_value)
           10: log_max_tx_value       — log(1 + max_tx_value)
           11: tx_velocity            — min(tx_velocity_per_day / 100.0, 1.0)
           12: has_token_transfers    — 1.0 / 0.0
           13: concentration_index    — 1 - unique_party_ratio (high = concentrated)
        """
        total_tx = max(incoming_count + outgoing_count, 1)
        in_out_ratio = incoming_count / total_tx if total_tx > 0 else 0.5
        unique_ratio = min(unique_counterparties / max(tx_count, 1), 1.0)

        return [
            math.log1p(tx_count),
            math.log1p(total_value_eth),
            in_out_ratio,
            unique_ratio,
            1.0 if is_contract else 0.0,
            math.log1p(age_days),
            min(mixer_exposure_pct / 100.0, 1.0),
            1.0 if is_sanctioned else 0.0,
            min(risk_score / 100.0, 1.0),
            math.log1p(avg_tx_value),
            math.log1p(max_tx_value),
            min(tx_velocity_per_day / 100.0, 1.0),
            1.0 if has_token_transfers else 0.0,
            1.0 - unique_ratio,
        ]

    # --- Transaction Features ---
    @staticmethod
    def extract_transaction_features(
        value_eth: float,
        gas_used: float,
        gas_price_gwei: float,
        block_number: int,
        hour_of_day: int,
        day_of_week: int,
        is_to_contract: bool,
        input_data_length: int,
        sender_tx_count: int,
        receiver_tx_count: int,
        sender_risk_score: int = 0,
        receiver_risk_score: int = 0,
    ) -> List[float]:
        """
        Produces a normalized 12-dimensional feature vector for transaction fraud detection.
        """
        return [
            math.log1p(value_eth),
            math.log1p(gas_used),
            math.log1p(gas_price_gwei),
            math.log1p(block_number) / 20.0,
            hour_of_day / 23.0,
            day_of_week / 6.0,
            1.0 if is_to_contract else 0.0,
            math.log1p(input_data_length),
            math.log1p(sender_tx_count),
            math.log1p(receiver_tx_count),
            min(sender_risk_score / 100.0, 1.0),
            min(receiver_risk_score / 100.0, 1.0),
        ]

    # --- Case Features ---
    @staticmethod
    def extract_case_features(
        wallet_count: int,
        evidence_count: int,
        age_days: int,
        priority_numeric: int,
        total_risk_score: float,
        has_sanctioned_wallet: bool,
        has_mixer_exposure: bool,
        alert_count: int,
    ) -> List[float]:
        """
        Produces an 8-dimensional feature vector for case prioritization models.
        """
        return [
            math.log1p(wallet_count),
            math.log1p(evidence_count),
            math.log1p(age_days),
            min(priority_numeric / 4.0, 1.0),
            min(total_risk_score / 100.0, 1.0),
            1.0 if has_sanctioned_wallet else 0.0,
            1.0 if has_mixer_exposure else 0.0,
            math.log1p(alert_count),
        ]

    # --- Alert Features ---
    @staticmethod
    def extract_alert_features(
        severity_numeric: int,
        risk_score: int,
        alert_type_encoded: int,
        time_since_last_alert_hours: float,
        related_wallet_risk: int,
        is_repeated_pattern: bool,
    ) -> List[float]:
        """
        Produces a 6-dimensional feature vector for alert prioritization.
        """
        return [
            min(severity_numeric / 4.0, 1.0),
            min(risk_score / 100.0, 1.0),
            min(alert_type_encoded / 10.0, 1.0),
            min(math.log1p(time_since_last_alert_hours) / 10.0, 1.0),
            min(related_wallet_risk / 100.0, 1.0),
            1.0 if is_repeated_pattern else 0.0,
        ]

    # --- Encoding Helpers ---
    @staticmethod
    def encode_priority(priority: str) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(priority.lower(), 2)

    @staticmethod
    def encode_severity(severity: str) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(severity.lower(), 2)

    @staticmethod
    def encode_alert_type(alert_type: str) -> int:
        type_map = {
            "balance": 1, "incoming": 2, "outgoing": 3,
            "brute_force_attack": 4, "session_hijack": 5,
            "large_transfer": 6, "mixer_interaction": 7,
            "sanctioned_hit": 8, "peel_chain": 9,
        }
        return type_map.get(alert_type.lower(), 0)


feature_store = FeatureStore()
