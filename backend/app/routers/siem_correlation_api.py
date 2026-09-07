"""
LEATrace SIEM Correlation Router — Production.

Correlation engine, attack chain reconstruction, and risk history.

PRODUCTION INVARIANTS:
- No random.randint() in risk scores.
- Mock events pool retained for default test stream but clearly labeled.
- Risk history from real database alert data.
"""

import datetime
import logging
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..correlation_engine import siem_correlation
from ..attack_chain_engine import attack_chain
from ..database import get_db
from .. import models, security

logger = logging.getLogger("leatrace.routers.siem")

router = APIRouter(prefix="/api/correlation", tags=["SIEM Correlation & Attack Reconstruction"])

# Default event stream for testing (clearly labeled as sample data)
SAMPLE_EVENTS = [
    {"event_type": "auth_fail", "timestamp": 1782720000, "description": "Failed investigator login from untrusted IP"},
    {"event_type": "auth_fail", "timestamp": 1782720010, "description": "Failed investigator login from untrusted IP"},
    {"event_type": "auth_fail", "timestamp": 1782720020, "description": "Failed investigator login from untrusted IP"},
    {"event_type": "evidence_download", "timestamp": 1782720050, "description": "Investigator downloaded evidence case logs"},
    {"event_type": "large_transfer", "timestamp": 1782720100, "description": "Large transfer to mixer contract detected"},
]


@router.post("/run")
def run_correlation_stream(events: Optional[List[Dict[str, Any]]] = Body(None)):
    """Runs SIEM correlation on a provided event stream or sample data."""
    stream = events if events else SAMPLE_EVENTS
    alerts = siem_correlation.correlate_event_stream(stream)
    return {
        "status": "completed",
        "alerts_triggered": len(alerts),
        "alerts": alerts,
        "data_source": "user_provided" if events else "sample_events",
    }


@router.get("/alerts")
def get_soc_alerts():
    """Returns correlation alert history."""
    return siem_correlation.get_alerts_history()


@router.get("/attack-chain")
def get_reconstructed_chain(correlation_id: str = Query(...)):
    """Reconstructs attack chain timeline from correlation data."""
    return attack_chain.reconstruct_incident_chain(correlation_id, SAMPLE_EVENTS)


@router.get("/risk/history")
def get_risk_scoring_history(db: Session = Depends(get_db)):
    """
    Returns risk scoring history based on real alert data from the database.
    No random values — counts real alerts by severity and date.
    """
    today = datetime.date.today()
    risk_trends = []

    for days_ago in range(3, -1, -1):
        target_date = today - datetime.timedelta(days=days_ago)
        start = datetime.datetime.combine(target_date, datetime.time.min)
        end = datetime.datetime.combine(target_date, datetime.time.max)

        # Count alerts by severity for this date
        critical_count = db.query(models.Alert).filter(
            models.Alert.created_at >= start,
            models.Alert.created_at <= end,
            models.Alert.severity == "critical",
        ).count()

        high_count = db.query(models.Alert).filter(
            models.Alert.created_at >= start,
            models.Alert.created_at <= end,
            models.Alert.severity == "high",
        ).count()

        total_count = db.query(models.Alert).filter(
            models.Alert.created_at >= start,
            models.Alert.created_at <= end,
        ).count()

        # Risk scores derived from real alert counts
        user_risk = min(critical_count * 25 + high_count * 10 + total_count * 2, 100)
        infra_risk = min(critical_count * 15 + high_count * 5, 100)

        risk_trends.append({
            "date": target_date.isoformat(),
            "user_risk": user_risk,
            "infrastructure_risk": infra_risk,
            "alert_count": total_count,
        })

    return {"risk_trends": risk_trends, "data_source": "alert_database"}
