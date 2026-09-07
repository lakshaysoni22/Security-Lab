from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import datetime
import httpx

from database.connection import get_db, Base, engine
from database import models
from shared import schemas
from config.settings import settings
from shared.logger import logger

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Investigation & Forensics Service", version="1.0.0")

# --- Schemas ---
class CaseCreateRequest(BaseModel):
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    assigned_to: str = "Inspector Verma"

class CaseResponse(BaseModel):
    case_id: str
    title: str
    status: str
    priority: str
    assigned_to: str
    created_at: str

class FraudCheckRequest(BaseModel):
    transaction_id: str
    amount: float
    mixer_used: bool
    rapid_transactions: bool

class FraudCheckResponse(BaseModel):
    transaction_id: str
    fraud_score: float
    status: str
    analysis: str

class ForensicReportRequest(BaseModel):
    case_id: str
    wallet_address: str

class ForensicReportResponse(BaseModel):
    case_id: str
    evidence_package: List[Dict[str, Any]]
    final_risk_score: float
    report_summary: str
    created_at: str

# --- Graph Engine & Models (Optional networkx fallback) ---
try:
    import networkx as nx
    def build_evidence_graph(connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        G = nx.DiGraph()
        for conn in connections:
            G.add_edge(conn["from"], conn["to"], weight=conn.get("value", 1.0))
        return {
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "density": nx.density(G)
        }
except ImportError:
    def build_evidence_graph(connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        nodes = set()
        for conn in connections:
            nodes.add(conn["from"])
            nodes.add(conn["to"])
        return {
            "node_count": len(nodes),
            "edge_count": len(connections),
            "density": 0.5
        }

# --- API Endpoints ---

@app.post("/investigation/cases/create", response_model=CaseResponse)
def create_case(request: CaseCreateRequest, db: Session = Depends(get_db)):
    logger.info(f"Creating new forensic case: {request.title}")
    
    case_id = str(uuid.uuid4())
    case_number = f"CC-2026-{str(uuid.uuid4())[:4].upper()}"
    
    new_case = models.Case(
        id=case_id,
        case_number=case_number,
        title=request.title,
        description=request.description,
        priority=request.priority,
        status="under_investigation",
        investigator_name=request.assigned_to,
        department="Cyber Crime Cell"
    )
    
    db.add(new_case)
    db.commit()
    
    return CaseResponse(
        case_id=case_id,
        title=request.title,
        status="under_investigation",
        priority=request.priority,
        assigned_to=request.assigned_to,
        created_at=datetime.datetime.utcnow().isoformat()
    )

@app.post("/investigation/detect-fraud", response_model=FraudCheckResponse)
async def detect_fraud(request: FraudCheckRequest):
    logger.info(f"Analyzing transaction for fraud: {request.transaction_id}")
    
    # 1. Rule-based Fraud Score Calculation
    score = 0.1
    if request.amount > 10000:
        score += 0.4
    if request.mixer_used:
        score += 0.4
    if request.rapid_transactions:
        score += 0.2
        
    score = min(score, 1.0)
    
    # 2. AI-based Core Decision via CPOS (simulated microservice call)
    ai_status = "STABLE"
    try:
        async with httpx.AsyncClient() as client:
            cpos_res = await client.post(
                f"{settings.CPOS_SERVICE_URL}/cpos/process",
                json={"input": f"Analyze transaction {request.transaction_id} for high-risk pattern.", "mode": "deep"}
            )
            if cpos_res.status_code == 200:
                cpos_data = cpos_res.json()
                if cpos_data.get("decision") == "flagged":
                    score = max(score, 0.6)
                    ai_status = "MEDIUM_RISK"
                elif cpos_data.get("decision") == "blocked":
                    score = max(score, 0.9)
                    ai_status = "HIGH_RISK"
    except Exception as e:
        logger.error(f"Failed to query CPOS engine: {e}")
        
    status = "LOW_RISK"
    if score >= 0.8:
        status = "HIGH_RISK"
    elif score >= 0.4:
        status = "MEDIUM_RISK"
        
    analysis = f"Analysis complete. Score resolved at {score} based on Rule+AI constraints."
    return FraudCheckResponse(
        transaction_id=request.transaction_id,
        fraud_score=score,
        status=status,
        analysis=analysis
    )

@app.post("/investigation/forensic-report", response_model=ForensicReportResponse)
async def generate_forensic_report(request: ForensicReportRequest, db: Session = Depends(get_db)):
    logger.info(f"Generating Master Forensic Intelligence Report for case: {request.case_id}")
    
    # 1. Query Case details
    case = db.query(models.Case).filter(models.Case.id == request.case_id).first()
    if not case:
        # Check if fallback seed CC-2026-0847 is targeted
        case = db.query(models.Case).filter(models.Case.case_number == request.case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Forensic case not found")
            
    # 2. Fetch Blockchain Traces (simulated microservice call)
    connections = []
    blockchain_risk = 0.1
    try:
        async with httpx.AsyncClient() as client:
            bc_res = await client.post(
                f"{settings.BLOCKCHAIN_SERVICE_URL}/blockchain/trace",
                json={"address": request.wallet_address, "depth": 3}
            )
            if bc_res.status_code == 200:
                bc_data = bc_res.json()
                connections = bc_data.get("connections", [])
                blockchain_risk = bc_data.get("risk_score", 0.1)
    except Exception as e:
        logger.error(f"Failed to query Blockchain Intelligence service: {e}")
        
    # 3. Calculate graph metrics
    graph_metrics = build_evidence_graph(connections)
    
    evidence_package = [
        {
            "type": "blockchain_connection_network",
            "nodes_count": graph_metrics["node_count"],
            "edges_count": graph_metrics["edge_count"],
            "density": graph_metrics["density"]
        },
        {
            "type": "investigator_case_briefing",
            "title": case.title,
            "status": case.status,
            "assigned": case.investigator_name or "Inspector Verma"
        }
    ]
    
    summary = f"Forensic analysis compiled for case {case.case_number}. Identified {graph_metrics['node_count']} nodes across {graph_metrics['edge_count']} transactions. Overall risk factor calculated at {blockchain_risk}."
    
    return ForensicReportResponse(
        case_id=case.id,
        evidence_package=evidence_package,
        final_risk_score=blockchain_risk,
        report_summary=summary,
        created_at=datetime.datetime.utcnow().isoformat()
    )
