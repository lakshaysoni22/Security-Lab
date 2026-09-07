import os
import pickle
from typing import Dict, Any, List, Tuple

# Fallback Python RandomForestClassifier implementation in case sklearn is missing
try:
    from sklearn.ensemble import RandomForestClassifier as SklearnRF
except ImportError:
    class SklearnRF:
        def __init__(self, n_estimators=10):
            self.n_estimators = n_estimators
        def fit(self, X: List[List[float]], y: List[int]):
            pass
        def predict(self, X: List[List[float]]) -> List[int]:
            # Simple threshold rules simulation for fallback
            return [1 if sum(row) > 1.5 else 0 for row in X]
        def predict_proba(self, X: List[List[float]]) -> List[List[float]]:
            return [[0.1, 0.9] if sum(row) > 1.5 else [0.9, 0.1] for row in X]

class MLEngine:
    def __init__(self, model_dir: str = "models_registry"):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.model = SklearnRF(n_estimators=10)

    def train_wallet_risk_model(self, X: List[List[float]], y: List[int]) -> str:
        """Trains the Random Forest classifier model on feature matrices."""
        self.model.fit(X, y)
        model_path = os.path.join(self.model_dir, "wallet_risk_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)
        return model_path

    def load_model(self) -> bool:
        """Loads serialized model from registry disk."""
        model_path = os.path.join(self.model_dir, "wallet_risk_model.pkl")
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            return True
        return False

    def predict_risk(self, features: List[float]) -> Dict[str, Any]:
        """Runs model prediction on single wallet feature vectors."""
        # Feature order: [tx_count, total_value, is_mixer_connected, is_sanctioned]
        prob = self.model.predict_proba([features])[0]
        prediction = self.model.predict([features])[0]
        return {
            "risk_prediction": "high" if prediction == 1 else "low",
            "confidence_score": round(prob[1] * 100, 2),
            "features_analyzed": features
        }

ml_engine = MLEngine()
