"""
LEAtTrace AI Platform — Anomaly Detection Model.

Isolation Forest for unsupervised anomaly detection on wallet feature vectors.
Identifies statistical outliers that deviate from normal wallet behavior patterns.
"""

import datetime
from typing import List, Dict, Any
from .base_model import BaseModel

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AnomalyDetectionModel(BaseModel):
    MODEL_NAME = "anomaly_detector"
    MODEL_VERSION = "1.0.0"
    FEATURE_DIM = 14

    def __init__(self):
        super().__init__()
        if SKLEARN_AVAILABLE:
            self.model = IsolationForest(
                n_estimators=200, contamination=0.08,
                max_features=0.8, random_state=42
            )
        else:
            self.model = None

    def train(self, X: List[List[float]], y: List[int] = None) -> Dict[str, float]:
        if self.model is None:
            self.is_trained = True
            self.training_timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
            self.training_metrics = {"n_samples": len(X), "contamination": 0.08, "framework": "fallback"}
            return self.training_metrics

        self.model.fit(X)
        self.is_trained = True
        self.training_timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"

        predictions = self.model.predict(X)
        n_anomalies = sum(1 for p in predictions if p == -1)
        scores = self.model.decision_function(X)

        self.training_metrics = {
            "n_samples": len(X),
            "n_anomalies_detected": n_anomalies,
            "anomaly_rate": round(n_anomalies / len(X), 4),
            "mean_anomaly_score": round(float(sum(scores) / len(scores)), 4),
            "contamination": 0.08,
        }
        return self.training_metrics

    def predict(self, features: List[float]) -> Dict[str, Any]:
        if self.model and self.is_trained:
            score = float(self.model.decision_function([features])[0])
            prediction = int(self.model.predict([features])[0])
            is_anomaly = prediction == -1
        else:
            import math
            score = -(features[6] * 0.3 + features[7] * 0.25 + features[8] * 0.2) if len(features) >= 14 else -0.1
            is_anomaly = score < -0.3

        severity = "critical" if score < -0.5 else "high" if score < -0.3 else "medium" if score < -0.1 else "normal"
        return {
            "prediction": -1 if is_anomaly else 1,
            "is_anomaly": is_anomaly,
            "anomaly_score": round(score, 4),
            "severity": severity,
            "model": self.MODEL_NAME,
            "version": self.MODEL_VERSION,
        }

    def predict_batch(self, X: List[List[float]]) -> List[Dict[str, Any]]:
        return [self.predict(f) for f in X]
