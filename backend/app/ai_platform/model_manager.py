"""
LEAtTrace AI Platform — Model Manager.

Centralized lifecycle manager for all ML models. Handles loading, unloading,
health checking, and coordinating inference across the model fleet.
"""

import os
import datetime
from typing import Dict, Any, Optional, List

from .config import ai_config
from .models.wallet_risk_model import WalletRiskModel
from .models.fraud_detection_model import FraudDetectionModel
from .models.laundering_detection_model import LaunderingDetectionModel
from .models.anomaly_detection_model import AnomalyDetectionModel
from .models.wallet_clustering_model import WalletClusteringModel
from .models.alert_prioritizer_model import AlertPrioritizerModel
from .models.specialized_models import (
    ThreatClassifierModel, EntityResolutionModel,
    CrossChainFraudModel, BehavioralAnalyticsModel
)


class ModelManager:
    """
    Central registry and lifecycle manager for all ML models.
    Handles model loading from disk, in-memory caching, and fleet health.
    """

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self):
        """Instantiates all model objects (does not load weights)."""
        if self._initialized:
            return

        self._models = {
            "wallet_risk_scorer": WalletRiskModel(),
            "transaction_fraud_detector": FraudDetectionModel(),
            "laundering_detector": LaunderingDetectionModel(),
            "anomaly_detector": AnomalyDetectionModel(),
            "wallet_clustering": WalletClusteringModel(),
            "alert_prioritizer": AlertPrioritizerModel(),
            "threat_classifier": ThreatClassifierModel(),
            "entity_resolver": EntityResolutionModel(),
            "cross_chain_fraud": CrossChainFraudModel(),
            "behavioral_analytics": BehavioralAnalyticsModel(),
        }
        self._initialized = True

    def load_all_models(self) -> Dict[str, bool]:
        """Attempts to load trained weights for all registered models."""
        self.initialize()
        results = {}
        for name, model in self._models.items():
            model_path = os.path.join(
                ai_config.model_registry_path,
                f"{name}_v{model.MODEL_VERSION}.pkl"
            )
            loaded = model.load(model_path)
            results[name] = loaded
        return results

    def get_model(self, model_name: str):
        """Returns a model instance by name."""
        self.initialize()
        return self._models.get(model_name)

    def list_models(self) -> List[Dict[str, Any]]:
        """Returns status of all registered models."""
        self.initialize()
        return [
            {
                "model_name": name,
                "model_version": model.MODEL_VERSION,
                "is_trained": model.is_trained,
                "feature_dim": model.FEATURE_DIM,
                "training_timestamp": model.training_timestamp,
                "has_metrics": bool(model.training_metrics),
            }
            for name, model in self._models.items()
        ]

    def get_health(self) -> Dict[str, Any]:
        """Returns health status of all models."""
        self.initialize()
        total = len(self._models)
        trained = sum(1 for m in self._models.values() if m.is_trained)
        return {
            "total_models": total,
            "trained_models": trained,
            "untrained_models": total - trained,
            "health_status": "healthy" if trained == total else "degraded" if trained > 0 else "offline",
            "models": {
                name: {
                    "is_trained": model.is_trained,
                    "version": model.MODEL_VERSION,
                    "accuracy": model.training_metrics.get("accuracy"),
                }
                for name, model in self._models.items()
            },
            "checked_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        }

    def predict(self, model_name: str, features: List[float]) -> Dict[str, Any]:
        """Runs inference on a specific model."""
        model = self.get_model(model_name)
        if model is None:
            return {"error": f"Model '{model_name}' not found"}
        return model.predict(features)

    def get_model_metrics(self, model_name: str) -> Dict[str, Any]:
        """Returns training metrics for a specific model."""
        model = self.get_model(model_name)
        if model is None:
            return {"error": f"Model '{model_name}' not found"}
        return model.get_metrics()


# Singleton instance
model_manager = ModelManager()
