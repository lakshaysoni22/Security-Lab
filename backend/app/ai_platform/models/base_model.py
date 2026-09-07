"""
LEAtTrace AI Platform — Base Model Interface.

Abstract base class for all ML models in the platform.
Provides consistent train/evaluate/predict/export interface.
"""

import os
import pickle
import json
import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

from ..config import ai_config


class BaseModel(ABC):
    """Abstract base class for all LEAtTrace ML models."""

    MODEL_NAME: str = "base_model"
    MODEL_VERSION: str = "1.0.0"
    FEATURE_DIM: int = 0

    def __init__(self):
        self.model = None
        self.is_trained = False
        self.training_metrics: Dict[str, float] = {}
        self.training_timestamp: Optional[str] = None
        self.model_path: Optional[str] = None

    @abstractmethod
    def train(self, X: List[List[float]], y: Optional[List[int]] = None) -> Dict[str, float]:
        """Train the model. Returns metrics dict."""
        pass

    @abstractmethod
    def predict(self, features: List[float]) -> Dict[str, Any]:
        """Run inference on a single feature vector."""
        pass

    @abstractmethod
    def predict_batch(self, X: List[List[float]]) -> List[Dict[str, Any]]:
        """Run inference on a batch of feature vectors."""
        pass

    def evaluate(self, X: List[List[float]], y: List[int]) -> Dict[str, float]:
        """Evaluate model performance on a test set."""
        if not self.is_trained:
            return {"error": "Model not trained"}

        predictions = [self.predict(x) for x in X]
        y_pred = [p.get("prediction", 0) for p in predictions]

        metrics = self._compute_classification_metrics(y, y_pred)
        return metrics

    def save(self, path: Optional[str] = None) -> str:
        """Serialize model to disk."""
        if path is None:
            path = os.path.join(ai_config.model_registry_path, f"{self.MODEL_NAME}_v{self.MODEL_VERSION}.pkl")

        os.makedirs(os.path.dirname(path), exist_ok=True)

        model_data = {
            "model": self.model,
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "is_trained": self.is_trained,
            "training_metrics": self.training_metrics,
            "training_timestamp": self.training_timestamp,
            "feature_dim": self.FEATURE_DIM,
        }

        with open(path, "wb") as f:
            pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)

        # Save metadata JSON alongside
        meta_path = path.replace(".pkl", "_metadata.json")
        meta = {
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "feature_dim": self.FEATURE_DIM,
            "is_trained": self.is_trained,
            "training_metrics": self.training_metrics,
            "training_timestamp": self.training_timestamp,
            "saved_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
            "file_path": path,
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        self.model_path = path
        return path

    def load(self, path: Optional[str] = None) -> bool:
        """Deserialize model from disk."""
        if path is None:
            path = os.path.join(ai_config.model_registry_path, f"{self.MODEL_NAME}_v{self.MODEL_VERSION}.pkl")

        if not os.path.exists(path):
            return False

        with open(path, "rb") as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.is_trained = model_data.get("is_trained", True)
        self.training_metrics = model_data.get("training_metrics", {})
        self.training_timestamp = model_data.get("training_timestamp")
        self.model_path = path
        return True

    def get_metrics(self) -> Dict[str, Any]:
        """Returns model performance metrics."""
        return {
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "is_trained": self.is_trained,
            "training_metrics": self.training_metrics,
            "training_timestamp": self.training_timestamp,
        }

    def _compute_classification_metrics(
        self, y_true: List[int], y_pred: List[int]
    ) -> Dict[str, float]:
        """Computes accuracy, precision, recall, F1 for classification tasks."""
        n = len(y_true)
        if n == 0:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        accuracy = correct / n

        # For binary: positive class = 1
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
        tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "true_negatives": tn,
            "total_samples": n,
        }
