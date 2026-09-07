"""
LEATrace SOC Dashboard Router — Production.

Real system metrics using psutil (if available), database query counts,
and actual connection states instead of random-generated mock data.

PRODUCTION INVARIANTS:
- No random.randint() or random.uniform() in any metric.
- All metrics from real system measurements or database queries.
"""

import datetime
import logging
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, security

logger = logging.getLogger("leatrace.routers.soc")

router = APIRouter(prefix="/api/soc", tags=["SOC Operations Center"])

# Try to import psutil for real system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.info("psutil not installed. SOC dashboard will report limited system metrics.")


def format_iso(dt: datetime.datetime) -> str:
    return dt.isoformat() + "Z"


@router.get("/dashboard")
def get_soc_dashboard(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Returns full SOC dashboard metrics from database."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    active_cases      = db.query(models.Case).filter(models.Case.status.in_(["open", "active", "under_investigation"])).count()
    open_alerts       = db.query(models.Alert).filter(models.Alert.is_read == False).count()
    critical_alerts   = db.query(models.Alert).filter(models.Alert.is_read == False, models.Alert.severity == "critical").count()
    total_wallets     = db.query(models.Wallet).count()
    total_evidence    = db.query(models.Evidence).count()
    closed_cases      = db.query(models.Case).filter(models.Case.status == "closed").count()
    cases_this_month  = db.query(models.Case).filter(models.Case.created_at >= month_start).count()
    high_risk_wallets = db.query(models.Wallet).filter(models.Wallet.risk_score >= 70).count()
    team_members      = db.query(models.User).filter(models.User.is_active == True).count()

    return {
        "timestamp":        format_iso(now),
        "active_cases":     active_cases,
        "open_alerts":      open_alerts,
        "critical_alerts":  critical_alerts,
        "total_wallets":    total_wallets,
        "total_evidence":   total_evidence,
        "closed_cases":     closed_cases,
        "cases_this_month": cases_this_month,
        "high_risk_wallets": high_risk_wallets,
        "team_members":     team_members,
        "data_source":      "database",
    }


@router.get("/recent-events")
def get_recent_events(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Returns recent audit log events from the database."""
    recent_logs = db.query(models.AuditLog).order_by(
        models.AuditLog.timestamp.desc()
    ).limit(10).all()

    events = [
        {
            "id": log.id,
            "user": log.username,
            "action": log.action,
            "status": log.status,
            "timestamp": log.timestamp.isoformat() + "Z" if log.timestamp else None,
        }
        for log in recent_logs
    ]
    return {"events": events, "total": len(events)}


@router.get("/activity")
def get_weekly_activity(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """
    Returns 7-day investigation activity (traces, alerts, evidence) from audit logs.
    Groups audit log entries by day of week and action type.
    """
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    week_ago = now - datetime.timedelta(days=7)

    # Pull last 7 days of audit logs
    recent = db.query(models.AuditLog).filter(
        models.AuditLog.timestamp >= week_ago
    ).all()

    # Aggregate by day name
    day_map: dict = {}
    for log in recent:
        day = log.timestamp.strftime("%a") if log.timestamp else "Unknown"
        if day not in day_map:
            day_map[day] = {"day": day, "traces": 0, "alerts": 0, "evidence": 0}
        action = (log.action or "").lower()
        if "trace" in action or "wallet" in action:
            day_map[day]["traces"] += 1
        elif "alert" in action:
            day_map[day]["alerts"] += 1
        elif "evidence" in action:
            day_map[day]["evidence"] += 1

    # Order by weekday
    ordered_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    result = [day_map.get(d, {"day": d, "traces": 0, "alerts": 0, "evidence": 0}) for d in ordered_days]
    return result


@router.get("/correlation-summary")
def get_correlation_summary(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Returns real correlation summary from database state."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    total_wallets = db.query(models.Wallet).count()
    total_cases = db.query(models.Case).count()
    watchlist_count = db.query(models.WatchlistEntry).count()

    return {
        "correlation_id": f"CORR-{now.strftime('%Y%m%d%H%M')}",
        "total_wallets_tracked": total_wallets,
        "total_cases": total_cases,
        "watchlist_entries": watchlist_count,
        "timestamp": format_iso(now),
    }


@router.get("/threat-metrics")
def get_threat_metrics(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Returns real threat metrics from entity labels and alerts."""
    sanctioned_entities = db.query(models.EntityLabel).filter(
        models.EntityLabel.category == "sanctioned"
    ).count()
    scam_entities = db.query(models.EntityLabel).filter(
        models.EntityLabel.category == "scam"
    ).count()

    return {
        "sanctioned_entities_tracked": sanctioned_entities,
        "scam_entities_tracked": scam_entities,
        "total_entity_labels": db.query(models.EntityLabel).count(),
    }


@router.get("/system-health")
def get_system_health(current_user: models.User = Depends(security.get_current_user)):
    """Returns real system health metrics using psutil (if available)."""
    health = {
        "timestamp": format_iso(datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)),
    }

    if PSUTIL_AVAILABLE:
        health.update({
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_mb_used": round(psutil.virtual_memory().used / (1024 * 1024), 1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage("C:\\").percent,
        })
    else:
        health.update({
            "cpu_percent": None,
            "memory_mb_used": None,
            "memory_percent": None,
            "disk_percent": None,
            "note": "psutil not installed — install for real system metrics",
        })

    return health


@router.get("/observability")
def get_observability(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    """Returns observability data from real audit logs."""
    recent_logs = db.query(models.AuditLog).order_by(
        models.AuditLog.timestamp.desc()
    ).limit(5).all()

    log_entries = []
    for log in recent_logs:
        log_entries.append({
            "timestamp": log.timestamp.isoformat() + "Z" if log.timestamp else None,
            "level": "warning" if log.status == "warning" else "info",
            "message": log.action,
        })

    return {
        "recent_logs": log_entries,
        "data_source": "audit_log_database",
    }
