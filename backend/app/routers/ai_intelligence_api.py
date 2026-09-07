from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from ..ml_engine import ml_engine
from ..vector_service import vector_service
from ..model_server import model_server

router = APIRouter(prefix="/api/ai", tags=["AI/ML Forensics Intelligence"])

# Seed some mock documents for semantic searches on startup
vector_service.add_document("doc_001", "Tornado Cash mixer contract laundering alerts", {"source": "threat_intel"})
vector_service.add_document("doc_002", "Investigator logs downloaded evidence for cases in department 4", {"source": "audit"})
vector_service.add_document("doc_003", "Phishing email link compromised investigator session key", {"source": "incident"})

@router.post("/predict")
def predict_wallet_risk(features: List[float] = Body(..., description="[tx_count, total_value, is_mixer_connected, is_sanctioned]")):
    if len(features) != 4:
        raise HTTPException(status_code=400, detail="Feature vector must contain exactly 4 float metrics")
    return ml_engine.predict_risk(features)

@router.post("/train")
def train_classification_model(
    X: List[List[float]] = Body(...),
    y: List[int] = Body(...)
):
    try:
        path = ml_engine.train_wallet_risk_model(X, y)
        return {"status": "trained", "saved_path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/vector-search")
def search_semantic_documents(
    query: str = Body(..., embed=True),
    limit: int = Query(5)
):
    return vector_service.search_similarity(query, limit)

@router.post("/copilot/explain")
def get_ai_copilot_explain(
    topic: str = Body(...),
    context: str = Body(...)
):
    # Simulated explainable AI summaries using configured prompt mappings
    return {
        "topic": topic,
        "ai_explanation": f"AI Copilot analysis for: {topic}. Under given context {context}, this wallet matches mixer laundering heuristics with high risk weight.",
        "confidence": 98.4
    }

@router.post("/models/promote")
def promote_registry_model(model_id: str = Query(...)):
    return model_server.promote_challenger_to_champion(model_id)

@router.post("/models/rollback")
def rollback_registry_model(
    model_id: str = Query(...),
    version: str = Query(...)
):
    return model_server.rollback_model_version(model_id, version)
