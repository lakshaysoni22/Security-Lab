"""
LEAtTrace AI Platform — Experiment Tracker.

Local file-based experiment tracking system compatible with MLflow log format.
Tracks training runs, hyperparameters, metrics, and model artifacts.
"""

import os
import json
import datetime
import uuid
from typing import Dict, Any, Optional, List

from .config import ai_config


class ExperimentRun:
    """Represents a single training experiment run."""

    def __init__(self, experiment_name: str, run_name: str, base_path: str):
        self.experiment_name = experiment_name
        self.run_name = run_name
        self.run_id = uuid.uuid4().hex[:12]
        self.start_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        self.end_time: Optional[str] = None
        self.status = "RUNNING"
        self.params: Dict[str, Any] = {}
        self.metrics: Dict[str, float] = {}
        self.tags: Dict[str, str] = {}
        self.artifacts: List[str] = []

        self.run_dir = os.path.join(base_path, experiment_name, self.run_id)
        os.makedirs(self.run_dir, exist_ok=True)

    def log_param(self, key: str, value: Any):
        self.params[key] = value

    def log_params(self, params: Dict[str, Any]):
        self.params.update(params)

    def log_metric(self, key: str, value: float):
        self.metrics[key] = round(value, 6)

    def log_metrics(self, metrics: Dict[str, float]):
        for k, v in metrics.items():
            self.metrics[k] = round(v, 6)

    def set_tag(self, key: str, value: str):
        self.tags[key] = value

    def log_artifact(self, artifact_path: str):
        self.artifacts.append(artifact_path)

    def end_run(self, status: str = "COMPLETED"):
        self.end_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        self.status = status
        self._save()

    def _save(self):
        run_data = {
            "run_id": self.run_id,
            "experiment_name": self.experiment_name,
            "run_name": self.run_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "params": self.params,
            "metrics": self.metrics,
            "tags": self.tags,
            "artifacts": self.artifacts,
        }
        filepath = os.path.join(self.run_dir, "run_metadata.json")
        with open(filepath, "w") as f:
            json.dump(run_data, f, indent=2)


class ExperimentTracker:
    """Manages experiment tracking across all model training runs."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or ai_config.experiment_tracking_path
        os.makedirs(self.base_path, exist_ok=True)

    def start_run(self, experiment_name: str, run_name: str = "default") -> ExperimentRun:
        """Creates and returns a new experiment run."""
        return ExperimentRun(experiment_name, run_name, self.base_path)

    def list_experiments(self) -> List[str]:
        """Returns all experiment names."""
        if not os.path.exists(self.base_path):
            return []
        return [
            d for d in os.listdir(self.base_path)
            if os.path.isdir(os.path.join(self.base_path, d))
        ]

    def list_runs(self, experiment_name: str) -> List[Dict[str, Any]]:
        """Returns metadata for all runs in an experiment."""
        exp_dir = os.path.join(self.base_path, experiment_name)
        if not os.path.exists(exp_dir):
            return []

        runs = []
        for run_dir_name in os.listdir(exp_dir):
            meta_path = os.path.join(exp_dir, run_dir_name, "run_metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    runs.append(json.load(f))

        return sorted(runs, key=lambda r: r.get("start_time", ""), reverse=True)

    def get_best_run(self, experiment_name: str, metric: str = "accuracy", maximize: bool = True) -> Optional[Dict[str, Any]]:
        """Returns the run with the best value for the specified metric."""
        runs = self.list_runs(experiment_name)
        completed = [r for r in runs if r.get("status") == "COMPLETED" and metric in r.get("metrics", {})]
        if not completed:
            return None
        return max(completed, key=lambda r: r["metrics"][metric]) if maximize else min(completed, key=lambda r: r["metrics"][metric])

    def get_run(self, experiment_name: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Returns metadata for a specific run."""
        meta_path = os.path.join(self.base_path, experiment_name, run_id, "run_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                return json.load(f)
        return None


experiment_tracker = ExperimentTracker()
