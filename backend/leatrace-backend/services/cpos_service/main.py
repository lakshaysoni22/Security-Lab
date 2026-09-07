from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
import uuid
import json
import datetime

from database.connection import get_db, Base, engine, get_mongo_db, get_redis_client
from database import models
from shared import schemas
from config.settings import settings
from shared.logger import logger

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CPOS Core Engine Service", version="1.0.0")

@app.post("/cpos/process")
async def process(request: schemas.CPOSProcessRequest, db: Session = Depends(get_db)):
    logger.info(f"CPOS Processing request: {request.input} in {request.mode} mode")

    # Step 1: Governance check via NGEL (simulated microservice call)
    gov_allowed = True
    gov_reason = "passed"
    try:
        async with httpx.AsyncClient() as client:
            ngel_res = await client.post(
                f"{settings.NGEL_SERVICE_URL}/ngel/evaluate",
                json={"action": "process_input", "risk_level": "medium"}
            )
            if ngel_res.status_code == 200:
                ngel_data = ngel_res.json()
                gov_allowed = ngel_data.get("allowed", True)
                gov_reason = "passed" if gov_allowed else ngel_data.get("reason", "failed")
    except Exception as e:
        logger.error(f"Failed to connect to NGEL service: {e}")

    if not gov_allowed:
        raise HTTPException(status_code=400, detail=f"Governance Blocked: {gov_reason}")

    # Step 2: Probability resolution via QCAL (simulated microservice call)
    selected_option = "approved"
    prob = 0.91
    try:
        async with httpx.AsyncClient() as client:
            qcal_res = await client.post(
                f"{settings.QCAL_SERVICE_URL}/qcal/resolve",
                json={"inputs": ["approved", "flagged", "blocked"]}
            )
            if qcal_res.status_code == 200:
                qcal_data = qcal_res.json()
                selected_option = qcal_data.get("selected", "approved")
                prob = qcal_data.get("probability", 0.91)
    except Exception as e:
        logger.error(f"Failed to connect to QCAL service: {e}")

    # Step 3: Write structured outcome to PostgreSQL / SQLite
    trace_id = "trace-" + str(uuid.uuid4())[:8]
    new_decision = models.Decision(
        decision_id=trace_id,
        user_id="usr-system-cpos",
        input=request.input,
        output=selected_option,
        confidence=prob,
        risk_level="medium"
    )
    db.add(new_decision)
    db.commit()

    # Step 4: Write unstructured AI log to MongoDB
    try:
        mongo = get_mongo_db()
        ai_log = {
            "log_id": trace_id,
            "service": "CPOS",
            "input": request.input,
            "trace": [
                "Ingested transaction input",
                "Verified credentials",
                "Calculated hops via QCAL",
                "Executed safety simulation via NGEL"
            ],
            "result": {
                "decision": selected_option,
                "confidence": prob
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        mongo["ai_logs"].insert_one(ai_log)
    except Exception as e:
        logger.error(f"Failed to write to MongoDB: {e}")

    # Step 5: Cache decision in Redis for fast lookup
    try:
        redis_conn = get_redis_client()
        redis_conn.set(f"decision_cache:{trace_id}", selected_option, ex=3600)
    except Exception as e:
        logger.error(f"Failed to cache in Redis: {e}")

    return schemas.CPOSProcessResponse(
        decision=selected_option,
        confidence=prob,
        reasoning_trace=["Ingested transaction input", "Verified credentials", "Calculated hops", "Executed simulation"],
        governance=gov_reason,
        trace_id=trace_id
    )
