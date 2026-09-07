"""
LEAtTrace AI Platform — Training Pipeline.

Orchestrates end-to-end training: dataset generation → feature extraction →
model training → evaluation → experiment tracking → model persistence.
"""

import datetime
from typing import Dict, Any, Optional, List

from .config import ai_config
from .dataset_manager import dataset_manager
from .experiment_tracker import experiment_tracker
from .model_manager import model_manager


class TrainingPipeline:
    """Orchestrates model training with dataset generation and experiment tracking."""

    def train_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Trains all 10 models with synthetic datasets and tracks experiments."""
        model_manager.initialize()
        results = {}

        # 1. Wallet Risk Model
        results["wallet_risk_scorer"] = self._train_wallet_risk()

        # 2. Transaction Fraud Detector
        results["transaction_fraud_detector"] = self._train_fraud_detection()

        # 3. Alert Prioritizer
        results["alert_prioritizer"] = self._train_alert_prioritizer()

        # 4. Anomaly Detector (unsupervised)
        results["anomaly_detector"] = self._train_anomaly_detector()

        # 5. Wallet Clustering (unsupervised)
        results["wallet_clustering"] = self._train_wallet_clustering()

        # 6. Laundering Detector
        results["laundering_detector"] = self._train_laundering_detector()

        # 7-10. Specialized models (use wallet features)
        results["threat_classifier"] = self._train_threat_classifier()
        results["behavioral_analytics"] = self._train_behavioral_analytics()

        return results

    def train_single_model(self, model_name: str) -> Dict[str, Any]:
        """Trains a single model by name."""
        model_manager.initialize()
        training_methods = {
            "wallet_risk_scorer": self._train_wallet_risk,
            "transaction_fraud_detector": self._train_fraud_detection,
            "alert_prioritizer": self._train_alert_prioritizer,
            "anomaly_detector": self._train_anomaly_detector,
            "wallet_clustering": self._train_wallet_clustering,
            "laundering_detector": self._train_laundering_detector,
            "threat_classifier": self._train_threat_classifier,
            "behavioral_analytics": self._train_behavioral_analytics,
        }
        trainer = training_methods.get(model_name)
        if not trainer:
            return {"error": f"No training pipeline for model '{model_name}'"}
        return trainer()

    def _train_wallet_risk(self) -> Dict[str, Any]:
        run = experiment_tracker.start_run("wallet_risk_scorer", "auto_train")
        model = model_manager.get_model("wallet_risk_scorer")

        X, y = dataset_manager.generate_wallet_risk_dataset(n_samples=2000)
        split = int(len(X) * (1 - ai_config.test_split_ratio))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        run.log_params({"n_train": len(X_train), "n_test": len(X_test), "feature_dim": 14})

        train_metrics = model.train(X_train, y_train)
        test_metrics = model.evaluate(X_test, y_test)

        run.log_metrics({"train_" + k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})
        run.log_metrics({"test_" + k: v for k, v in test_metrics.items() if isinstance(v, (int, float))})

        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")

        return {"train_metrics": train_metrics, "test_metrics": test_metrics, "model_path": model_path}

    def _train_fraud_detection(self) -> Dict[str, Any]:
        run = experiment_tracker.start_run("transaction_fraud_detector", "auto_train")
        model = model_manager.get_model("transaction_fraud_detector")

        X, y = dataset_manager.generate_transaction_fraud_dataset(n_samples=3000)
        split = int(len(X) * (1 - ai_config.test_split_ratio))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        run.log_params({"n_train": len(X_train), "n_test": len(X_test)})
        train_metrics = model.train(X_train, y_train)
        test_metrics = model.evaluate(X_test, y_test)

        run.log_metrics({"train_" + k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})
        run.log_metrics({"test_" + k: v for k, v in test_metrics.items() if isinstance(v, (int, float))})

        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")
        return {"train_metrics": train_metrics, "test_metrics": test_metrics, "model_path": model_path}

    def _train_alert_prioritizer(self) -> Dict[str, Any]:
        run = experiment_tracker.start_run("alert_prioritizer", "auto_train")
        model = model_manager.get_model("alert_prioritizer")

        X, y = dataset_manager.generate_alert_priority_dataset(n_samples=1500)
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        run.log_params({"n_train": len(X_train), "n_test": len(X_test)})
        train_metrics = model.train(X_train, y_train)
        test_metrics = model.evaluate(X_test, y_test)

        run.log_metrics({"train_" + k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})
        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")
        return {"train_metrics": train_metrics, "test_metrics": test_metrics, "model_path": model_path}

    def _train_anomaly_detector(self) -> Dict[str, Any]:
        run = experiment_tracker.start_run("anomaly_detector", "auto_train")
        model = model_manager.get_model("anomaly_detector")

        X = dataset_manager.generate_anomaly_dataset(n_samples=2000)
        run.log_params({"n_samples": len(X)})

        train_metrics = model.train(X)
        run.log_metrics({k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})

        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")
        return {"train_metrics": train_metrics, "model_path": model_path}

    def _train_wallet_clustering(self) -> Dict[str, Any]:
        run = experiment_tracker.start_run("wallet_clustering", "auto_train")
        model = model_manager.get_model("wallet_clustering")

        X = dataset_manager.generate_anomaly_dataset(n_samples=1000)
        run.log_params({"n_samples": len(X)})

        train_metrics = model.train(X)
        run.log_metrics({k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})

        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")
        return {"train_metrics": train_metrics, "model_path": model_path}

    def _train_laundering_detector(self) -> Dict[str, Any]:
        import random
        run = experiment_tracker.start_run("laundering_detector", "auto_train")
        model = model_manager.get_model("laundering_detector")

        rng = random.Random(42)
        X, y = [], []
        for _ in range(1500):
            is_laundering = rng.random() < 0.3
            from .models.laundering_detection_model import LaunderingDetectionModel
            if is_laundering:
                feats = LaunderingDetectionModel.extract_laundering_features(
                    hop_count=rng.randint(5, 30), total_value=rng.uniform(100, 50000),
                    avg_hop_value=rng.uniform(10, 5000), value_decrease_ratio=rng.uniform(0.5, 0.95),
                    time_span_hours=rng.uniform(1, 48), unique_intermediaries=rng.randint(3, 20),
                    has_mixer=rng.random() < 0.6, has_cross_chain=rng.random() < 0.4,
                    round_amounts_ratio=rng.uniform(0.3, 0.9), sender_risk=rng.randint(50, 100)
                )
            else:
                feats = LaunderingDetectionModel.extract_laundering_features(
                    hop_count=rng.randint(1, 5), total_value=rng.uniform(0.1, 100),
                    avg_hop_value=rng.uniform(0.05, 50), value_decrease_ratio=rng.uniform(0.0, 0.3),
                    time_span_hours=rng.uniform(0.1, 24), unique_intermediaries=rng.randint(1, 3),
                    has_mixer=False, has_cross_chain=False,
                    round_amounts_ratio=rng.uniform(0.0, 0.2), sender_risk=rng.randint(0, 30)
                )
            X.append(feats)
            y.append(1 if is_laundering else 0)

        split = int(len(X) * 0.8)
        train_metrics = model.train(X[:split], y[:split])
        test_metrics = model.evaluate(X[split:], y[split:])

        run.log_params({"n_train": split, "n_test": len(X) - split})
        run.log_metrics({"train_" + k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})

        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")
        return {"train_metrics": train_metrics, "test_metrics": test_metrics, "model_path": model_path}

    def _train_threat_classifier(self) -> Dict[str, Any]:
        run = experiment_tracker.start_run("threat_classifier", "auto_train")
        model = model_manager.get_model("threat_classifier")

        X, y = dataset_manager.generate_wallet_risk_dataset(n_samples=1500)
        # Remap binary labels to multi-class for threat classification
        import random
        rng = random.Random(42)
        y_multi = []
        for label in y:
            if label == 1:
                y_multi.append(rng.choice([1, 2, 3, 4, 5]))
            else:
                y_multi.append(0)

        split = int(len(X) * 0.8)
        train_metrics = model.train(X[:split], y_multi[:split])

        run.log_params({"n_train": split})
        run.log_metrics({k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})

        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")
        return {"train_metrics": train_metrics, "model_path": model_path}

    def _train_behavioral_analytics(self) -> Dict[str, Any]:
        run = experiment_tracker.start_run("behavioral_analytics", "auto_train")
        model = model_manager.get_model("behavioral_analytics")

        X = dataset_manager.generate_anomaly_dataset(n_samples=1000)
        train_metrics = model.train(X)

        run.log_params({"n_samples": len(X)})
        run.log_metrics({k: v for k, v in train_metrics.items() if isinstance(v, (int, float))})

        model_path = model.save()
        run.log_artifact(model_path)
        run.end_run("COMPLETED")
        return {"train_metrics": train_metrics, "model_path": model_path}


training_pipeline = TrainingPipeline()
