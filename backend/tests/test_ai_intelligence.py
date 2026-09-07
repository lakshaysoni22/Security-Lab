import pytest
import os
from app.ml_engine import ml_engine
from app.vector_service import vector_service
from app.model_server import model_server

def test_ml_model_training_and_inference():
    # 1. Dummy wallet features matrix: [tx_count, total_value, is_mixer_connected, is_sanctioned]
    X_train = [
        [100, 15.0, 1.0, 1.0], # high risk
        [5, 0.2, 0.0, 0.0],   # low risk
        [80, 25.5, 1.0, 0.0],  # high risk
        [2, 0.05, 0.0, 0.0]   # low risk
    ]
    y_train = [1, 0, 1, 0]
    
    # 2. Train model
    model_path = ml_engine.train_wallet_risk_model(X_train, y_train)
    assert os.path.exists(model_path)
    
    # 3. Load model
    assert ml_engine.load_model() is True
    
    # 4. Predict risk (high risk payload)
    res_high = ml_engine.predict_risk([90.0, 12.0, 1.0, 1.0])
    assert res_high["risk_prediction"] == "high"
    assert res_high["confidence_score"] > 50.0
    
    # 5. Predict risk (low risk payload)
    res_low = ml_engine.predict_risk([1.0, 0.01, 0.0, 0.0])
    assert res_low["risk_prediction"] == "low"

def test_faiss_semantic_vector_search():
    vector_service.add_document("doc_test_1", "sanctioned entities listing crypto addresses")
    vector_service.add_document("doc_test_2", "laundering tornado cash mixer transaction")
    
    # Search query matching tornado mixer
    matches = vector_service.search_similarity("tornado mixer transaction", limit=1)
    assert len(matches) == 1
    assert matches[0]["id"] == "doc_test_2"
    assert matches[0]["score"] > 0.0

def test_model_server_promotions_and_rollbacks():
    # Promote challenger to champion
    res_promote = model_server.promote_challenger_to_champion("wallet_risk")
    assert res_promote["status"] == "promoted"
    assert res_promote["new_champion"] == "v1.1.0-alpha"
    
    # Rollback version
    res_rollback = model_server.rollback_model_version("wallet_risk", "v1.0.0")
    assert res_rollback["status"] == "rolled_back"
    assert res_rollback["active_version"] == "v1.0.0"
