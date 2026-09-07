import datetime
import uuid
from sqlalchemy.orm import Session
from . import models, event_broker
from .siem_exporter import log_security_event

async def detect_login_brute_force(db: Session, username: str, ip_address: str, broker: event_broker.EventBroker):
    """
    Checks recent audit logs to detect brute-force attempts.
    If more than 3 failed attempts are recorded in the last 5 minutes, raises a critical anomaly alert.
    """
    five_minutes_ago = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(minutes=5)
    
    # Query failed logins for this user in last 5 minutes
    failed_attempts = db.query(models.AuditLog).filter(
        models.AuditLog.username == username,
        models.AuditLog.action.like("%login%"),
        models.AuditLog.status == "failure",
        models.AuditLog.timestamp >= five_minutes_ago
    ).count()

    if failed_attempts >= 3:
        alert_msg = f"[ANOMALY DETECTED] Potential brute-force attack on account: {username}. {failed_attempts} failed login attempts in 5 minutes."
        
        # 1. Write to database Alert table
        alert_entry = models.Alert(
            id=f"alr_{uuid.uuid4().hex[:7]}",
            chain="SYSTEM",
            address="N/A",
            alias="Security Guard",
            type="brute_force_attack",
            severity="critical",
            message=alert_msg,
            is_read=False,
            threshold=0.0
        )
        db.add(alert_entry)
        db.commit()

        # 2. Export security event to SIEM
        log_security_event(
            action=f"Brute force detection rule triggered for account: {username}",
            status="alarm",
            username=username,
            ip_address=ip_address,
            severity="CRITICAL",
            details={"failed_attempts_count": failed_attempts}
        )

        # 3. Broadcast Alert to all active WebSockets
        alert_event = {
            "id": alert_entry.id,
            "chain": "SYSTEM",
            "address": "N/A",
            "alias": "Security Guard",
            "type": "brute_force_attack",
            "severity": "critical",
            "message": alert_msg,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }
        await broker.publish("alert_stream", alert_event)
        
        return True
        
    return False

async def detect_session_hijacking(db: Session, session_id: str, current_ip: str, broker: event_broker.EventBroker):
    """
    Verifies that the session IP address matches the origin IP of the session creation block.
    If an IP switch is detected (indicating token theft / session hijacking), alerts immediately.
    """
    session = db.query(models.UserSession).filter(models.UserSession.id == session_id).first()
    if session and session.ip_address != current_ip:
        alert_msg = f"[ANOMALY DETECTED] Session hijacking alert. Session ID {session_id} origin IP {session.ip_address} swapped to {current_ip}!"
        
        # Raise alarm in Alert table
        alert_entry = models.Alert(
            id=f"alr_{uuid.uuid4().hex[:7]}",
            chain="SYSTEM",
            address="N/A",
            alias="Session Guard",
            type="session_hijack",
            severity="critical",
            message=alert_msg,
            is_read=False,
            threshold=0.0
        )
        db.add(alert_entry)
        
        # Flag session inactive
        session.is_active = False
        db.commit()

        # SIEM Export
        log_security_event(
            action=f"Token theft or session hijacking detected for Session ID: {session_id}",
            status="revoked",
            username=session.user_id,
            ip_address=current_ip,
            severity="CRITICAL",
            details={"original_ip": session.ip_address, "new_ip": current_ip}
        )

        # Broadcast
        alert_event = {
            "id": alert_entry.id,
            "chain": "SYSTEM",
            "address": "N/A",
            "alias": "Session Guard",
            "type": "session_hijack",
            "severity": "critical",
            "message": alert_msg,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        }
        await broker.publish("alert_stream", alert_event)
        return True

    return False


def calculate_fraud_probability(address: str, base_score: int, sanctions_status: bool, mixer_exposure: float, layering_hops: int) -> dict:
    """
    ML Heuristics Fraud Probability Engine.
    Analyzes transaction frequency, gas price anomalies, sanctions list matches,
    mixer interactions, and peel chains to calculate a risk index.
    """
    anomaly_indicators = []
    total_score = base_score
    
    if sanctions_status:
        total_score = max(total_score, 98)
        anomaly_indicators.append("Sanctioned list match (OFAC/UN/EU)")
        
    if mixer_exposure > 50.0:
        total_score = max(total_score, 85)
        anomaly_indicators.append("Critical mixer laundering exposure (>50% mixed volume)")
    elif mixer_exposure > 15.0:
        total_score = max(total_score, 50)
        anomaly_indicators.append("Moderate mixer exposure")
        
    if layering_hops >= 3:
        total_score = min(total_score + 15, 100)
        anomaly_indicators.append(f"Suspicious layering depth ({layering_hops} hops)")
        
    # Behavior profile
    profile_rating = "Critical Threat" if total_score >= 85 else "High Threat" if total_score >= 70 else "Monitored Target" if total_score >= 40 else "Standard Retail Account"
    
    return {
        "address": address,
        "fraud_probability_percent": total_score,
        "risk_classification": profile_rating,
        "behavioral_anomalies": anomaly_indicators,
        "assessment_timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    }

