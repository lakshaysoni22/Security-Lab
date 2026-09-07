"""
LEAtTrace AI Platform — Dataset Manager.

Generates training datasets from the existing SQLite/Postgres database
and produces synthetic augmentation data for model training.
"""

import random
import math
import datetime
from typing import List, Tuple, Dict, Any, Optional

from .feature_store import feature_store


class DatasetManager:
    """Generates ML-ready datasets from database records and synthetic augmentation."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    # -----------------------------------------------------------------
    # Wallet Risk Dataset
    # -----------------------------------------------------------------
    def generate_wallet_risk_dataset(
        self, n_samples: int = 2000
    ) -> Tuple[List[List[float]], List[int]]:
        """
        Generates a labeled wallet risk dataset.
        Label: 1 = high-risk, 0 = low-risk.
        """
        X, y = [], []

        for _ in range(n_samples):
            is_high_risk = self.rng.random() < 0.35

            if is_high_risk:
                tx_count = self.rng.randint(50, 5000)
                total_value = self.rng.uniform(10.0, 50000.0)
                incoming = self.rng.randint(20, 2500)
                outgoing = tx_count - incoming if tx_count > incoming else self.rng.randint(10, 500)
                unique_parties = self.rng.randint(3, min(tx_count, 50))
                is_contract = self.rng.random() < 0.3
                age_days = self.rng.randint(1, 365)
                mixer_exposure = self.rng.uniform(15.0, 95.0)
                is_sanctioned = self.rng.random() < 0.4
                risk_score = self.rng.randint(60, 100)
                avg_tx = total_value / max(tx_count, 1)
                max_tx = total_value * self.rng.uniform(0.3, 0.8)
                velocity = tx_count / max(age_days, 1)
                has_tokens = self.rng.random() < 0.7
            else:
                tx_count = self.rng.randint(1, 200)
                total_value = self.rng.uniform(0.01, 100.0)
                incoming = self.rng.randint(1, max(tx_count // 2, 1))
                outgoing = tx_count - incoming if tx_count > incoming else self.rng.randint(1, 20)
                unique_parties = self.rng.randint(1, min(tx_count, 30))
                is_contract = self.rng.random() < 0.1
                age_days = self.rng.randint(30, 1800)
                mixer_exposure = self.rng.uniform(0.0, 10.0)
                is_sanctioned = False
                risk_score = self.rng.randint(0, 40)
                avg_tx = total_value / max(tx_count, 1)
                max_tx = total_value * self.rng.uniform(0.05, 0.3)
                velocity = tx_count / max(age_days, 1)
                has_tokens = self.rng.random() < 0.4

            features = feature_store.extract_wallet_features(
                tx_count=tx_count,
                total_value_eth=total_value,
                incoming_count=incoming,
                outgoing_count=outgoing,
                unique_counterparties=unique_parties,
                is_contract=is_contract,
                age_days=age_days,
                mixer_exposure_pct=mixer_exposure,
                is_sanctioned=is_sanctioned,
                risk_score=risk_score,
                avg_tx_value=avg_tx,
                max_tx_value=max_tx,
                tx_velocity_per_day=velocity,
                has_token_transfers=has_tokens,
            )
            X.append(features)
            y.append(1 if is_high_risk else 0)

        return X, y

    # -----------------------------------------------------------------
    # Transaction Fraud Dataset
    # -----------------------------------------------------------------
    def generate_transaction_fraud_dataset(
        self, n_samples: int = 3000
    ) -> Tuple[List[List[float]], List[int]]:
        """
        Generates labeled transaction dataset.
        Label: 1 = fraudulent, 0 = legitimate.
        """
        X, y = [], []

        for _ in range(n_samples):
            is_fraud = self.rng.random() < 0.25

            if is_fraud:
                value = self.rng.uniform(5.0, 10000.0)
                gas_used = self.rng.uniform(21000, 500000)
                gas_price = self.rng.uniform(10, 500)
                block = self.rng.randint(18000000, 22000000)
                hour = self.rng.choice([0, 1, 2, 3, 4, 5, 22, 23])
                day = self.rng.randint(0, 6)
                is_to_contract = self.rng.random() < 0.6
                input_len = self.rng.randint(0, 5000)
                sender_tx = self.rng.randint(1, 20)
                receiver_tx = self.rng.randint(1, 10)
                sender_risk = self.rng.randint(50, 100)
                receiver_risk = self.rng.randint(30, 100)
            else:
                value = self.rng.uniform(0.001, 50.0)
                gas_used = self.rng.uniform(21000, 100000)
                gas_price = self.rng.uniform(5, 50)
                block = self.rng.randint(18000000, 22000000)
                hour = self.rng.randint(8, 20)
                day = self.rng.randint(0, 6)
                is_to_contract = self.rng.random() < 0.2
                input_len = self.rng.randint(0, 200)
                sender_tx = self.rng.randint(10, 5000)
                receiver_tx = self.rng.randint(10, 5000)
                sender_risk = self.rng.randint(0, 30)
                receiver_risk = self.rng.randint(0, 30)

            features = feature_store.extract_transaction_features(
                value_eth=value,
                gas_used=gas_used,
                gas_price_gwei=gas_price,
                block_number=block,
                hour_of_day=hour,
                day_of_week=day,
                is_to_contract=is_to_contract,
                input_data_length=input_len,
                sender_tx_count=sender_tx,
                receiver_tx_count=receiver_tx,
                sender_risk_score=sender_risk,
                receiver_risk_score=receiver_risk,
            )
            X.append(features)
            y.append(1 if is_fraud else 0)

        return X, y

    # -----------------------------------------------------------------
    # Alert Priority Dataset
    # -----------------------------------------------------------------
    def generate_alert_priority_dataset(
        self, n_samples: int = 1500
    ) -> Tuple[List[List[float]], List[int]]:
        """
        Generates labeled alert priority dataset.
        Labels: 0 = low, 1 = medium, 2 = high, 3 = critical.
        """
        X, y = [], []

        for _ in range(n_samples):
            label = self.rng.choices([0, 1, 2, 3], weights=[0.3, 0.3, 0.25, 0.15])[0]

            if label == 3:
                severity = 4
                risk = self.rng.randint(80, 100)
                alert_type = self.rng.choice([4, 5, 8])
                hours_since = self.rng.uniform(0.1, 2.0)
                wallet_risk = self.rng.randint(70, 100)
                repeated = self.rng.random() < 0.7
            elif label == 2:
                severity = self.rng.choice([3, 4])
                risk = self.rng.randint(50, 85)
                alert_type = self.rng.choice([6, 7, 9])
                hours_since = self.rng.uniform(0.5, 12.0)
                wallet_risk = self.rng.randint(40, 80)
                repeated = self.rng.random() < 0.5
            elif label == 1:
                severity = self.rng.choice([2, 3])
                risk = self.rng.randint(20, 55)
                alert_type = self.rng.choice([1, 2, 3])
                hours_since = self.rng.uniform(1.0, 48.0)
                wallet_risk = self.rng.randint(15, 50)
                repeated = self.rng.random() < 0.3
            else:
                severity = self.rng.choice([1, 2])
                risk = self.rng.randint(0, 25)
                alert_type = self.rng.choice([1, 2, 3])
                hours_since = self.rng.uniform(12.0, 168.0)
                wallet_risk = self.rng.randint(0, 25)
                repeated = self.rng.random() < 0.1

            features = feature_store.extract_alert_features(
                severity_numeric=severity,
                risk_score=risk,
                alert_type_encoded=alert_type,
                time_since_last_alert_hours=hours_since,
                related_wallet_risk=wallet_risk,
                is_repeated_pattern=repeated,
            )
            X.append(features)
            y.append(label)

        return X, y

    # -----------------------------------------------------------------
    # Anomaly Detection Dataset (unlabeled)
    # -----------------------------------------------------------------
    def generate_anomaly_dataset(
        self, n_samples: int = 2000
    ) -> List[List[float]]:
        """Generates unlabeled wallet feature vectors for anomaly detection."""
        X = []
        for _ in range(n_samples):
            is_anomaly = self.rng.random() < 0.08

            if is_anomaly:
                tx_count = self.rng.randint(500, 50000)
                total_value = self.rng.uniform(1000.0, 500000.0)
                mixer = self.rng.uniform(40.0, 99.0)
                risk = self.rng.randint(80, 100)
            else:
                tx_count = self.rng.randint(1, 500)
                total_value = self.rng.uniform(0.01, 200.0)
                mixer = self.rng.uniform(0.0, 5.0)
                risk = self.rng.randint(0, 40)

            features = feature_store.extract_wallet_features(
                tx_count=tx_count,
                total_value_eth=total_value,
                incoming_count=self.rng.randint(1, max(tx_count // 2, 1)),
                outgoing_count=self.rng.randint(1, max(tx_count // 2, 1)),
                unique_counterparties=self.rng.randint(1, min(tx_count, 100)),
                is_contract=self.rng.random() < 0.15,
                age_days=self.rng.randint(1, 1000),
                mixer_exposure_pct=mixer,
                is_sanctioned=is_anomaly and self.rng.random() < 0.3,
                risk_score=risk,
                avg_tx_value=total_value / max(tx_count, 1),
                max_tx_value=total_value * self.rng.uniform(0.1, 0.5),
                tx_velocity_per_day=tx_count / max(self.rng.randint(1, 365), 1),
                has_token_transfers=self.rng.random() < 0.5,
            )
            X.append(features)

        return X


dataset_manager = DatasetManager()
