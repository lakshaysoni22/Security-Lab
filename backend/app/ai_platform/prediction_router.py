"""
LEAtTrace AI Platform — Prediction & Training API Router.

FastAPI endpoints for model inference, training, health monitoring,
and experiment tracking. Integrates into the existing FastAPI app.
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel as PydanticModel

from ..ai_platform.model_manager import model_manager
from ..ai_platform.training_pipeline import training_pipeline
from ..ai_platform.feature_store import feature_store
from ..ai_platform.experiment_tracker import experiment_tracker


router = APIRouter(prefix="/api/ai", tags=["AI Platform"])


# --- Request/Response Models ---

class PredictionRequest(PydanticModel):
    model_name: str
    features: List[float]

class BatchPredictionRequest(PydanticModel):
    model_name: str
    feature_batch: List[List[float]]

class WalletRiskRequest(PydanticModel):
    tx_count: int = 100
    total_value_eth: float = 50.0
    incoming_count: int = 60
    outgoing_count: int = 40
    unique_counterparties: int = 15
    is_contract: bool = False
    age_days: int = 180
    mixer_exposure_pct: float = 5.0
    is_sanctioned: bool = False
    risk_score: int = 30
    avg_tx_value: float = 0.5
    max_tx_value: float = 10.0
    tx_velocity_per_day: float = 0.5
    has_token_transfers: bool = True

class TransactionFraudRequest(PydanticModel):
    value_eth: float = 1.0
    gas_used: float = 21000
    gas_price_gwei: float = 20.0
    block_number: int = 20000000
    hour_of_day: int = 14
    day_of_week: int = 2
    is_to_contract: bool = False
    input_data_length: int = 0
    sender_tx_count: int = 100
    receiver_tx_count: int = 50
    sender_risk_score: int = 10
    receiver_risk_score: int = 5

class TrainRequest(PydanticModel):
    model_name: Optional[str] = None


# --- Endpoints ---

@router.get("/health")
async def ai_health():
    """Returns health status of all AI models."""
    return model_manager.get_health()

@router.get("/models")
async def list_models():
    """Lists all registered AI models and their status."""
    return model_manager.list_models()

@router.get("/models/{model_name}/metrics")
async def get_model_metrics(model_name: str):
    """Returns training metrics for a specific model."""
    metrics = model_manager.get_model_metrics(model_name)
    if "error" in metrics:
        raise HTTPException(status_code=404, detail=metrics["error"])
    return metrics

@router.post("/predict")
async def predict(req: PredictionRequest):
    """Runs inference on a specific model with raw feature vector."""
    result = model_manager.predict(req.model_name, req.features)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.post("/predict/batch")
async def predict_batch(req: BatchPredictionRequest):
    """Runs batch inference on a specific model."""
    model = model_manager.get_model(req.model_name)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model '{req.model_name}' not found")
    results = model.predict_batch(req.feature_batch)
    return {"model": req.model_name, "predictions": results, "count": len(results)}

@router.post("/predict/wallet-risk")
async def predict_wallet_risk(req: WalletRiskRequest):
    """Predicts wallet risk using domain-specific input fields."""
    features = feature_store.extract_wallet_features(
        tx_count=req.tx_count, total_value_eth=req.total_value_eth,
        incoming_count=req.incoming_count, outgoing_count=req.outgoing_count,
        unique_counterparties=req.unique_counterparties, is_contract=req.is_contract,
        age_days=req.age_days, mixer_exposure_pct=req.mixer_exposure_pct,
        is_sanctioned=req.is_sanctioned, risk_score=req.risk_score,
        avg_tx_value=req.avg_tx_value, max_tx_value=req.max_tx_value,
        tx_velocity_per_day=req.tx_velocity_per_day,
        has_token_transfers=req.has_token_transfers,
    )
    return model_manager.predict("wallet_risk_scorer", features)

@router.post("/predict/transaction-fraud")
async def predict_transaction_fraud(req: TransactionFraudRequest):
    """Predicts transaction fraud using domain-specific input fields."""
    features = feature_store.extract_transaction_features(
        value_eth=req.value_eth, gas_used=req.gas_used,
        gas_price_gwei=req.gas_price_gwei, block_number=req.block_number,
        hour_of_day=req.hour_of_day, day_of_week=req.day_of_week,
        is_to_contract=req.is_to_contract, input_data_length=req.input_data_length,
        sender_tx_count=req.sender_tx_count, receiver_tx_count=req.receiver_tx_count,
        sender_risk_score=req.sender_risk_score,
        receiver_risk_score=req.receiver_risk_score,
    )
    return model_manager.predict("transaction_fraud_detector", features)

@router.post("/train")
async def train_models(req: TrainRequest):
    """Triggers model training. If model_name is provided, trains only that model."""
    if req.model_name:
        result = training_pipeline.train_single_model(req.model_name)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return {"model": req.model_name, "result": result}

    results = training_pipeline.train_all_models()
    return {
        "status": "training_complete",
        "models_trained": len(results),
        "results": results,
    }

@router.get("/experiments")
async def list_experiments():
    """Lists all experiment runs."""
    experiments = experiment_tracker.list_experiments()
    return {"experiments": experiments}

@router.get("/experiments/{experiment_name}")
async def get_experiment_runs(experiment_name: str):
    """Lists all runs for a specific experiment."""
    runs = experiment_tracker.list_runs(experiment_name)
    return {"experiment": experiment_name, "runs": runs}

@router.get("/experiments/{experiment_name}/best")
async def get_best_run(experiment_name: str, metric: str = "accuracy"):
    """Returns the best run for an experiment by a specific metric."""
    best = experiment_tracker.get_best_run(experiment_name, metric)
    if not best:
        raise HTTPException(status_code=404, detail="No completed runs found")
    return best
