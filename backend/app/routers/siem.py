"""
LEATrace SIEM Router — Production.

DB-backed security incident management, IOC lookups, correlation engine,
and anomaly detection. Optional OpenSearch/Elasticsearch forwarding.

PRODUCTION INVARIANTS:
- No hardcoded SECURITY_INCIDENTS list.
- No hardcoded IOC_THREAT_FEEDS dict.
- No fabricated kill-chain timelines.
- All data from database or real audit logs.
- IOC check uses sanctions_entries + stix_indicators tables.
- Correlation uses real AuditLog records.
- If OpenSearch not configured: DB-only mode (clearly stated).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import statistics
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, security
from ..threat_database import threat_db

logger = logging.getLogger("leatrace.routers.siem")

router = APIRouter(prefix="/api/siem", tags=["SIEM & SOC Operations"])

# Optional OpenSearch/Elasticsearch forwarding
OPENSEARCH_URL: Optional[str] = os.getenv("OPENSEARCH_URL")   # e.g. http://localhost:9200
OPENSEARCH_INDEX: str = os.getenv("OPENSEARCH_INDEX", "leatrace-incidents")


# ─── Schemas ──────────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    severity:         str
    category:         Optional[str] = None
    mitre_technique:  Optional[str] = None
    message:          str
    source:           Optional[str] = None
    source_ip:        Optional[str] = None
    related_address:  Optional[str] = None
    raw_event:        Optional[str] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _forward_to_opensearch(incident: models.SecurityIncident) -> None:
    """Optionally forwards incident to OpenSearch/Elasticsearch."""
    if not OPENSEARCH_URL:
        return
    try:
        import urllib.request
        doc = {
            "id":              incident.id,
            "severity":        incident.severity,
            "category":        incident.category,
            "message":         incident.message,
            "source":          incident.source,
            "status":          incident.status,
            "created_at":      incident.created_at.isoformat() + "Z" if incident.created_at else None,
        }
        data = json.dumps(doc).encode()
        req = urllib.request.Request(
            f"{OPENSEARCH_URL}/{OPENSEARCH_INDEX}/_doc/{incident.id}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.warning("OpenSearch forward failed: %s", e)


# ─── Incidents ────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=List[Dict[str, Any]])
def get_siem_alerts(
    status: Optional[str] = Query(None, description="Filter by status: open|acknowledged|closed"),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> List[Dict[str, Any]]:
    """
    Returns security incidents from the database.
    Supports filtering by status and severity.
    """
    query = db.query(models.SecurityIncident)
    if status:
        query = query.filter(models.SecurityIncident.status == status)
    if severity:
        query = query.filter(models.SecurityIncident.severity == severity)

    incidents = query.order_by(models.SecurityIncident.created_at.desc()).offset(skip).limit(limit).all()
    return [_serialize_incident(i) for i in incidents]


@router.post("/alerts", status_code=201)
def create_siem_alert(
    body: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Creates a new security incident in the DB and optionally forwards to OpenSearch."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    incident = models.SecurityIncident(
        id=str(uuid.uuid4()),
        severity=body.severity,
        category=body.category,
        mitre_technique=body.mitre_technique,
        message=body.message,
        source=body.source,
        source_ip=body.source_ip,
        related_address=body.related_address,
        raw_event=body.raw_event,
        status="open",
        created_at=now,
    )
    db.add(incident)

    # Audit log
    db.add(models.AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        username=current_user.username,
        action=f"CREATE_INCIDENT: {body.severity.upper()} — {body.message[:80]}",
        status="success",
        actor=current_user.username,
        validation_status="validated",
        created_at=now,
    ))
    db.commit()
    db.refresh(incident)

    _forward_to_opensearch(incident)
    return _serialize_incident(incident)


@router.post("/alerts/{incident_id}/assign")
def assign_incident(
    incident_id: str,
    payload: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Assigns a security incident to an analyst."""
    incident = _get_incident_or_404(incident_id, db)
    analyst = payload.get("analyst", "").strip()
    if not analyst:
        raise HTTPException(status_code=400, detail="analyst field required")

    incident.analyst_assigned = analyst
    incident.status = "acknowledged"
    incident.updated_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"status": "success", "message": f"Incident {incident_id} assigned to {analyst}"}


@router.post("/alerts/{incident_id}/status")
def update_incident_status(
    incident_id: str,
    payload: Dict[str, str] = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Updates the status of a security incident."""
    incident = _get_incident_or_404(incident_id, db)
    new_status = payload.get("status", "").strip()
    allowed = {"open", "acknowledged", "closed", "escalated"}
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {allowed}")

    incident.status = new_status
    incident.updated_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    if new_status == "closed":
        incident.closed_at = incident.updated_at
    db.commit()
    return {"status": "success", "message": f"Incident status → {new_status}"}


# ─── IOC Lookup ───────────────────────────────────────────────────────────────

@router.get("/threat-intel/ioc-check")
def scan_ioc_feeds(
    indicator: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """
    Checks an indicator (wallet address or IP) against:
    1. sanctions_entries table (OFAC SDN, EU Consolidated)
    2. stix_indicators table (TAXII synced indicators)

    Returns real match details or explicit "no match" result.
    Never uses hardcoded IOC list.
    """
    clean = indicator.strip().lower()

    sanction = threat_db.check_sanction(clean, db=db)
    stix_hit = threat_db.check_stix_indicator(clean, db=db)

    total_sanctions = db.query(models.SanctionsEntry).count()
    total_stix = db.query(models.StixIndicator).count()

    match_found = bool(sanction or stix_hit)
    response: Dict[str, Any] = {
        "indicator": indicator,
        "match_found": match_found,
        "sanction_match": sanction,
        "stix_match": stix_hit,
        "data_sources": {
            "sanctions_entries": total_sanctions,
            "stix_indicators": total_stix,
        },
    }

    if total_sanctions == 0 and total_stix == 0:
        response["notice"] = (
            "Both IOC databases are empty. "
            "Run POST /api/sanctions/sync and POST /api/taxii/sync to populate."
        )

    return response


# ─── Correlation ──────────────────────────────────────────────────────────────

@router.get("/correlation")
def get_log_correlation(
    wallet_address: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """
    Correlates real audit log events related to a wallet address.

    Queries AuditLog for events mentioning the address or recent high-severity actions.
    Returns real timestamps and actions — never fabricated timelines.
    """
    logs_query = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc())

    if wallet_address:
        # Filter logs mentioning the address
        logs = logs_query.filter(
            models.AuditLog.action.contains(wallet_address)
        ).limit(20).all()
        correlation_id = "COR-" + hashlib.sha256(wallet_address.encode()).hexdigest()[:8].upper()
    else:
        # Return last 20 security-relevant events
        logs = logs_query.limit(20).all()
        correlation_id = "COR-LATEST"

    timeline = []
    for idx, log in enumerate(logs):
        timeline.append({
            "step":      idx + 1,
            "timestamp": log.timestamp.isoformat() + "Z" if log.timestamp else None,
            "source":    "AuditLog",
            "event":     log.action,
            "actor":     log.username,
            "status":    log.status,
        })

    return {
        "correlation_id":   correlation_id,
        "correlated_entity": wallet_address or "all",
        "event_count":      len(timeline),
        "timeline_events":  timeline,
        "data_source":      "audit_log_database",
        "notice":           None if timeline else "No audit log events found for this query.",
    }


# ─── Anomaly Detection ────────────────────────────────────────────────────────

@router.get("/anomaly-detection")
def run_anomaly_detection(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """
    Runs Z-score anomaly detection on real API response times from audit logs.

    Queries the last 100 audit log timestamps and computes inter-event gaps
    as a proxy for anomalous activity bursts.
    Returns real statistical analysis — no hardcoded latency arrays.
    """
    logs = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.timestamp.isnot(None))
        .order_by(models.AuditLog.timestamp.desc())
        .limit(100)
        .all()
    )

    if len(logs) < 3:
        return {
            "status": "insufficient_data",
            "message": "Need at least 3 audit log entries to run anomaly detection.",
            "events_available": len(logs),
        }

    # Compute inter-event gaps in seconds as proxy for burst detection
    timestamps = sorted(
        [log.timestamp for log in logs if log.timestamp],
        reverse=False,
    )
    gaps = [
        (timestamps[i + 1] - timestamps[i]).total_seconds()
        for i in range(len(timestamps) - 1)
    ]

    if len(gaps) < 2:
        return {"status": "insufficient_data", "events_available": len(logs)}

    mean_gap = statistics.mean(gaps)
    stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0.0

    anomalies = []
    for idx, gap in enumerate(gaps):
        z = (gap - mean_gap) / stdev_gap if stdev_gap > 0 else 0.0
        if abs(z) > 2.5:
            anomalies.append({
                "gap_index":    idx,
                "gap_seconds":  round(gap, 3),
                "z_score":      round(z, 3),
                "severity":     "High" if abs(z) > 3.5 else "Medium",
                "timestamp":    timestamps[idx].isoformat() + "Z",
            })

    return {
        "status":              "active",
        "events_analyzed":     len(logs),
        "mean_gap_seconds":    round(mean_gap, 3),
        "std_dev_gap_seconds": round(stdev_gap, 3),
        "anomalies_detected":  len(anomalies),
        "anomalies":           anomalies,
        "data_source":         "audit_log_database",
    }


# ─── Health ───────────────────────────────────────────────────────────────────

@router.get("/health")
def siem_health(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Returns SIEM backend connectivity and configuration status."""
    db_ok = False
    incident_count = 0
    try:
        incident_count = db.query(models.SecurityIncident).count()
        db_ok = True
    except Exception as e:
        logger.error("SIEM health DB check failed: %s", e)

    opensearch_ok = None
    if OPENSEARCH_URL:
        try:
            import urllib.request
            with urllib.request.urlopen(f"{OPENSEARCH_URL}/_cluster/health", timeout=3) as r:
                opensearch_ok = r.status == 200
        except Exception:
            opensearch_ok = False

    return {
        "database":          "healthy" if db_ok else "error",
        "incident_count":    incident_count,
        "opensearch_url":    OPENSEARCH_URL,
        "opensearch_status": "healthy" if opensearch_ok else ("not_configured" if opensearch_ok is None else "unreachable"),
        "ioc_mode":          "database",
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_incident_or_404(incident_id: str, db: Session) -> models.SecurityIncident:
    inc = db.query(models.SecurityIncident).filter(models.SecurityIncident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


def _serialize_incident(i: models.SecurityIncident) -> Dict[str, Any]:
    return {
        "id":               i.id,
        "severity":         i.severity,
        "category":         i.category,
        "mitre_technique":  i.mitre_technique,
        "message":          i.message,
        "source":           i.source,
        "analyst_assigned": i.analyst_assigned,
        "status":           i.status,
        "source_ip":        i.source_ip,
        "related_address":  i.related_address,
        "created_at":       i.created_at.isoformat() + "Z" if i.created_at else None,
        "updated_at":       i.updated_at.isoformat() + "Z" if i.updated_at else None,
        "closed_at":        i.closed_at.isoformat() + "Z" if i.closed_at else None,
    }
