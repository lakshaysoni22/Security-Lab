import uuid
import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, security
from ..event_broker import broker

router = APIRouter(prefix="/api/incident", tags=["Incident Response System"])

class LockdownRequest(BaseModel):
    address: str
    chain: str
    notes: Optional[str] = None

@router.get("/threats")
def get_live_threats(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Fetches threat dashboard statistics, live streams, and prioritized incident boards."""
    # Count lockdowns
    lockdowns = db.query(models.WatchlistEntry).filter(models.WatchlistEntry.status == "LOCKED").all()
    lockdown_count = len(lockdowns)
    
    # Get recent critical/high alerts
    recent_threats = db.query(models.Alert).filter(
        models.Alert.severity.in_(["critical", "high"])
    ).order_by(models.Alert.created_at.desc()).limit(10).all()
    
    # Check threat level
    active_threat_level = "low"
    if db.query(models.Alert).filter(models.Alert.severity == "critical", models.Alert.is_read == False).count() > 0:
        active_threat_level = "critical"
    elif db.query(models.Alert).filter(models.Alert.severity == "high", models.Alert.is_read == False).count() > 0:
        active_threat_level = "high"
    elif db.query(models.Alert).filter(models.Alert.severity == "medium", models.Alert.is_read == False).count() > 0:
        active_threat_level = "medium"

    # Get prioritized cases
    cases = db.query(models.Case).all()
    # Sort cases custom priority: critical -> high -> medium -> low
    priority_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    sorted_cases = sorted(
        cases,
        key=lambda c: (priority_weights.get(c.priority.lower(), 2), c.updated_at),
        reverse=True
    )
    
    # Limit to top 15 cases
    prioritized_cases = []
    for c in sorted_cases[:15]:
        prioritized_cases.append({
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "priority": c.priority,
            "status": c.status,
            "updated_at": c.updated_at.isoformat() + "Z"
        })

    return {
        "active_threat_level": active_threat_level,
        "lockdown_count": lockdown_count,
        "locked_addresses": [{"address": l.address, "chain": l.chain} for l in lockdowns],
        "recent_threats": [
            {
                "id": t.id,
                "chain": t.chain,
                "address": t.address,
                "alias": t.alias,
                "type": t.type,
                "severity": t.severity,
                "message": t.message,
                "is_read": t.is_read,
                "created_at": t.created_at.isoformat() + "Z"
            }
            for t in recent_threats
        ],
        "prioritized_cases": prioritized_cases
    }

@router.post("/escalate")
async def trigger_escalation(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Scans and escalates unread critical/high threat alerts to supervisor queues."""
    unread_threats = db.query(models.Alert).filter(
        models.Alert.severity.in_(["critical", "high"]),
        models.Alert.is_read == False,
        models.Alert.status != "Escalated"
    ).all()

    escalated_count = 0
    escalation_messages = []

    for alert in unread_threats:
        alert.status = "Escalated"
        escalated_count += 1
        
        # Log to immutable audit log ledger
        audit_entry = models.AuditLog(
            id=f"log_{uuid.uuid4().hex[:7]}",
            user_id="System",
            username="Incident Response Engine",
            action=f"AUTOMATED ESCALATION: Alert ID {alert.id} for address {alert.address} escalated due to inaction.",
            status="warning",
            actor="System",
            decision_source="Incident Response Loop",
            validation_status="Verified"
        )
        db.add(audit_entry)

        # Trigger case priority escalation if case contains this wallet address
        linked_wallets = db.query(models.Wallet).filter(models.Wallet.address == alert.address).all()
        for w in linked_wallets:
            if w.case and w.case.priority != "critical":
                w.case.priority = "critical"
                db.add(w.case)

        # Publish escalation event to WebSocket alert stream
        esc_message = f"[SLA ESCALATION] Unresolved {alert.severity.upper()} threat on address {alert.address[:10]}... escalated to Tier-2 Command."
        escalation_messages.append(esc_message)
        
        esc_event = {
            "id": f"esc_{uuid.uuid4().hex[:7]}",
            "chain": alert.chain,
            "address": alert.address,
            "alias": alert.alias,
            "type": "escalation",
            "severity": "critical",
            "message": esc_message,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }
        await broker.publish("alert_stream", esc_event)

    if escalated_count > 0:
        db.commit()

    return {
        "escalated_count": escalated_count,
        "escalation_messages": escalation_messages
    }

@router.post("/prioritize-cases")
def run_case_prioritizer(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Analyzes threat scores & alerts across active cases to dynamically update prioritizations."""
    cases = db.query(models.Case).filter(models.Case.status != "closed").all()
    updated_count = 0

    for c in cases:
        old_priority = c.priority
        highest_score = 0
        has_critical_alert = False
        has_high_alert = False

        for w in c.wallets:
            if w.risk_score > highest_score:
                highest_score = w.risk_score
            
            # Check for active alerts on this address
            alerts = db.query(models.Alert).filter(models.Alert.address == w.address).all()
            for alert in alerts:
                if alert.severity == "critical":
                    has_critical_alert = True
                elif alert.severity == "high":
                    has_high_alert = True

        # Heuristic Priority Re-calibration
        new_priority = "low"
        if highest_score >= 80 or has_critical_alert:
            new_priority = "critical"
        elif highest_score >= 60 or has_high_alert:
            new_priority = "high"
        elif highest_score >= 30:
            new_priority = "medium"

        if c.priority != new_priority:
            c.priority = new_priority
            c.updated_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            updated_count += 1
            
            # Log adjustment
            audit_entry = models.AuditLog(
                id=f"log_{uuid.uuid4().hex[:7]}",
                user_id=current_user.id,
                username=current_user.username,
                action=f"PRIORITIZER: Recalibrated case {c.case_number} priority from '{old_priority}' to '{new_priority}'.",
                status="success",
                actor="AI",
                decision_source="Prioritization Engine",
                validation_status="Verified"
            )
            db.add(audit_entry)

    if updated_count > 0:
        db.commit()

    return {
        "scanned_cases_count": len(cases),
        "recalibrated_count": updated_count
    }

@router.post("/emergency-lockdown")
async def trigger_emergency_lockdown(req: LockdownRequest, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Triggers an absolute lockdown protocol: freezes on-chain monitoring, blocks transfers, and logs immutable forensics."""
    # Find or create watchlist entry
    watchlist_entry = db.query(models.WatchlistEntry).filter(
        models.WatchlistEntry.address == req.address
    ).first()

    if not watchlist_entry:
        watchlist_entry = models.WatchlistEntry(
            id=f"wtl-{uuid.uuid4().hex[:7]}",
            address=req.address,
            chain=req.chain,
            alias=f"LOCKED Suspect: {req.address[:8]}",
            risk_score=100,
            status="LOCKED"
        )
        db.add(watchlist_entry)
    else:
        watchlist_entry.status = "LOCKED"
        watchlist_entry.risk_score = 100

    # Log to immutable chain of custody & audit logs
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"EMERGENCY PROTOCOL SHIELD: Triggered lockdown for address {req.address} ({req.chain}). Reason: {req.notes or 'None'}",
        status="failure", # Force failure flag for high-priority security logs
        actor="Human",
        decision_source="Incident Response UI",
        validation_status="Verified"
    )
    db.add(audit_entry)

    # Publish lockdown alert to WebSocket stream
    lockdown_msg = f"[EMERGENCY LOCKDOWN] Suspicious address {req.address} ({req.chain}) has been LOCKED by IR Command!"
    lockdown_event = {
        "id": f"lock_{uuid.uuid4().hex[:7]}",
        "chain": req.chain,
        "address": req.address,
        "alias": watchlist_entry.alias,
        "type": "lockdown",
        "severity": "critical",
        "message": lockdown_msg,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    }
    await broker.publish("alert_stream", lockdown_event)

    db.commit()

    return {
        "status": "success",
        "message": "Emergency protocol shield activated. Address is locked in watchlist.",
        "address": req.address,
        "chain": req.chain
    }
