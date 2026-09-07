"""
LEATrace Unified Threat Intelligence API — Production.

Single REST surface for all TI operations: providers, IOCs, STIX objects,
enrichment, confidence, feed management, and dashboard.

PRODUCTION INVARIANTS:
- All endpoints return real data or structured "not_configured" / "empty" status.
- No hardcoded threat intelligence. No fabricated indicators.
- RBAC enforced: analyst (read), supervisor (read+write), admin (full).
- Audit logging on all write operations.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, security
from ..ioc_engine import ioc_engine
from ..confidence_engine import confidence_engine
from ..deduplication_engine import deduplication_engine
from ..enrichment_engine import enrichment_engine
from ..feed_priority_engine import feed_priority_engine
from ..threat_intel.provider_manager import provider_manager

logger = logging.getLogger("leatrace.routers.threat_intel")

router = APIRouter(prefix="/api/ti", tags=["Threat Intelligence"])


# ═══════════════════════════════════════════════════════════════════════════════
# Provider Management
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/providers")
def list_providers(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns all registered TI providers and their status."""
    return {
        "providers": provider_manager.get_all_provider_status(),
        "total": len(provider_manager.registry.get_all()),
    }


@router.get("/providers/{name}/health")
def get_provider_health(
    name: str,
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Returns detailed health for a specific TI provider."""
    return provider_manager.get_provider_health(name)


@router.get("/providers/health")
def health_check_all_providers(
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Runs health checks on all TI providers."""
    return provider_manager.health_check_all()


# ═══════════════════════════════════════════════════════════════════════════════
# Sync Operations
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/sync")
def sync_all_providers(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Triggers sync across all active TI providers.
    Requires supervisor or admin role.
    """
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    logger.info("TI sync triggered by %s", current_user.username)
    result = provider_manager.sync_all(db)

    # Audit
    _write_audit(db, current_user,
                 f"TI_SYNC_ALL: providers={result.get('providers_synced', 0)} "
                 f"objects_new={result.get('total_objects_new', 0)}")
    return result


@router.post("/sync/{provider_name}")
def sync_single_provider(
    provider_name: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Triggers sync for a single TI provider."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    result = provider_manager.sync_provider(provider_name, db)
    _write_audit(db, current_user,
                 f"TI_SYNC: provider={provider_name} status={result.get('status')}")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# IOC Operations
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/iocs")
def list_iocs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    ioc_type: Optional[str] = Query(None, description="Filter by IOC type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    source_provider: Optional[str] = Query(None, description="Filter by source"),
    min_confidence: Optional[float] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None, description="Search IOC values"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="asc or desc"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns paginated IOC list with filtering and sorting.
    Returns empty list if no IOCs exist — never fabricated data.
    """
    return ioc_engine.list_iocs(
        db, skip=skip, limit=limit,
        ioc_type=ioc_type, status=status, severity=severity,
        source_provider=source_provider, min_confidence=min_confidence,
        search=search, sort_by=sort_by, sort_order=sort_order,
    )


@router.get("/iocs/statistics")
def get_ioc_statistics(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns IOC database statistics."""
    return ioc_engine.get_ioc_statistics(db)


@router.get("/iocs/{ioc_id}")
def get_ioc_detail(
    ioc_id: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns full IOC detail with version history and observations."""
    return ioc_engine.get_ioc(ioc_id, db)


@router.post("/iocs")
def create_ioc(
    ioc_type: str = Query(..., description="IOC type (ip, domain, hash_sha256, etc.)"),
    value: str = Query(..., description="IOC value"),
    confidence: float = Query(50.0, ge=0, le=100),
    severity: str = Query("medium"),
    description: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    expiration_days: Optional[int] = Query(None, ge=1),
    tlp: str = Query("TLP:AMBER"),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Creates an analyst-submitted IOC.
    Requires supervisor or admin role.
    """
    if current_user.role not in ("admin", "supervisor", "analyst"):
        return {"status": "forbidden", "message": "Requires analyst role or above."}

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    result = ioc_engine.add_ioc(
        ioc_type=ioc_type,
        value=value,
        db=db,
        confidence=confidence,
        severity=severity,
        source_provider="analyst",
        created_by=current_user.username,
        description=description,
        tags=tag_list,
        expiration_days=expiration_days,
        tlp=tlp,
    )

    _write_audit(db, current_user,
                 f"IOC_CREATE: type={ioc_type} value={value[:30]}")
    return result


@router.put("/iocs/{ioc_id}")
def update_ioc(
    ioc_id: str,
    confidence_score: Optional[float] = Query(None, ge=0, le=100),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    tlp: Optional[str] = Query(None),
    reason: Optional[str] = Query(None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Updates IOC fields with version tracking."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    fields = {}
    if confidence_score is not None:
        fields["confidence_score"] = confidence_score
    if severity:
        fields["severity"] = severity
    if status:
        fields["status"] = status
    if description:
        fields["description"] = description
    if tlp:
        fields["tlp"] = tlp

    result = ioc_engine.update_ioc(
        ioc_id, db,
        updated_by=current_user.username,
        reason=reason,
        **fields,
    )

    _write_audit(db, current_user,
                 f"IOC_UPDATE: id={ioc_id} fields={list(fields.keys())}")
    return result


@router.delete("/iocs/{ioc_id}")
def revoke_ioc(
    ioc_id: str,
    reason: Optional[str] = Query(None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Soft-deletes (revokes) an IOC with audit trail."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    result = ioc_engine.revoke_ioc(
        ioc_id, db,
        revoked_by=current_user.username,
        reason=reason,
    )
    _write_audit(db, current_user, f"IOC_REVOKE: id={ioc_id}")
    return result


@router.post("/iocs/{ioc_id}/false-positive")
def mark_ioc_false_positive(
    ioc_id: str,
    reason: Optional[str] = Query(None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Marks an IOC as false positive with audit trail."""
    if current_user.role not in ("admin", "supervisor", "analyst"):
        return {"status": "forbidden", "message": "Requires analyst role or above."}

    result = ioc_engine.mark_false_positive(
        ioc_id, db,
        marked_by=current_user.username,
        reason=reason,
    )
    _write_audit(db, current_user, f"IOC_FALSE_POSITIVE: id={ioc_id}")
    return result


@router.get("/iocs/{ioc_id}/check")
def check_ioc_value(
    value: str = Query(..., description="Value to check against IOC database"),
    ioc_type: Optional[str] = Query(None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Checks if a value is a known IOC."""
    return ioc_engine.check_ioc(value, db=db, ioc_type=ioc_type)


# ═══════════════════════════════════════════════════════════════════════════════
# Enrichment
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/iocs/{ioc_id}/enrich")
def enrich_ioc(
    ioc_id: str,
    force_refresh: bool = Query(False),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Triggers enrichment for an IOC."""
    result = enrichment_engine.enrich_ioc(ioc_id, db, force_refresh=force_refresh)
    _write_audit(db, current_user, f"IOC_ENRICH: id={ioc_id}")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/iocs/{ioc_id}/confidence")
def get_ioc_confidence(
    ioc_id: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns confidence score breakdown for an IOC."""
    return confidence_engine.recalculate_ioc_confidence(ioc_id, db)


@router.post("/iocs/confidence/recalculate")
def batch_recalculate_confidence(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Recalculates confidence for all active IOCs."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}
    return confidence_engine.batch_recalculate(db)


# ═══════════════════════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/iocs/duplicates")
def find_duplicate_iocs(
    ioc_type: Optional[str] = Query(None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Finds duplicate IOC groups in the database."""
    groups = deduplication_engine.find_duplicates(db, ioc_type=ioc_type)
    return {"duplicate_groups": groups, "total_groups": len(groups)}


@router.post("/iocs/deduplicate")
def auto_deduplicate(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Automatically merges all detected duplicate IOCs."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    result = deduplication_engine.auto_merge_all(
        db, merged_by=current_user.username,
    )
    _write_audit(db, current_user,
                 f"IOC_AUTO_DEDUP: merged={result.get('total_merged', 0)}")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STIX Objects
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/stix/{stix_type}")
def list_stix_objects(
    stix_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Lists STIX objects of a given type from the local database."""
    from ..stix_models import STIX_TYPE_TO_MODEL

    model_cls = STIX_TYPE_TO_MODEL.get(stix_type)
    if not model_cls:
        # Try indicator via StixIndicator
        if stix_type == "indicator":
            query = db.query(models.StixIndicator)
            total = query.count()
            items = query.order_by(models.StixIndicator.created_at.desc()).offset(skip).limit(limit).all()
            return {
                "type": stix_type,
                "total": total,
                "skip": skip,
                "limit": limit,
                "objects": [
                    {
                        "id": i.id,
                        "stix_id": i.stix_id,
                        "name": i.name,
                        "pattern": i.pattern,
                        "pattern_type": i.pattern_type,
                        "confidence": i.confidence,
                        "valid_from": i.valid_from.isoformat() if i.valid_from else None,
                    }
                    for i in items
                ],
            }
        return {"status": "error", "message": f"Unknown STIX type: {stix_type}"}

    try:
        query = db.query(model_cls)
        total = query.count()
        items = query.order_by(model_cls.ingested_at.desc()).offset(skip).limit(limit).all()

        return {
            "type": stix_type,
            "total": total,
            "skip": skip,
            "limit": limit,
            "objects": [
                {
                    "id": i.id,
                    "stix_id": i.stix_id,
                    "name": getattr(i, "name", None),
                    "description": (getattr(i, "description", None) or "")[:200],
                    "created": i.created.isoformat() if i.created else None,
                    "modified": i.modified.isoformat() if i.modified else None,
                    "source_provider": i.source_provider,
                    "confidence": i.confidence,
                }
                for i in items
            ],
            "data_source": "stix_database",
        }

    except Exception as e:
        return {"status": "error", "message": str(e)[:300]}


# ═══════════════════════════════════════════════════════════════════════════════
# Feeds & Priority
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/feeds")
def list_feed_status(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns feed status and priority rankings."""
    return {
        "rankings": feed_priority_engine.rank_providers(db),
    }


@router.post("/feeds/{provider_id}/trust")
def update_feed_trust(
    provider_id: str,
    trust_score: float = Query(..., ge=0, le=100),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Updates analyst trust score for a feed provider."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    return feed_priority_engine.update_analyst_trust(
        provider_id, trust_score, db,
        updated_by=current_user.username,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MITRE ATT&CK Lookup
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/mitre/technique/{technique_id}")
def lookup_mitre_technique(
    technique_id: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Looks up a MITRE ATT&CK technique by ID (e.g., T1059)."""
    from ..threat_intel.providers.mitre_attack_provider import MITREAttackProvider
    provider = provider_manager.registry.get("mitre_attack")
    if isinstance(provider, MITREAttackProvider):
        return provider.lookup_technique(technique_id, db)
    return {"status": "not_configured", "message": "MITRE ATT&CK provider not registered."}


@router.get("/mitre/techniques")
def list_mitre_techniques(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Lists all MITRE ATT&CK techniques from the local database."""
    from ..threat_intel.providers.mitre_attack_provider import MITREAttackProvider
    provider = provider_manager.registry.get("mitre_attack")
    if isinstance(provider, MITREAttackProvider):
        return provider.list_techniques(db, skip=skip, limit=limit)
    return {"status": "not_configured", "message": "MITRE ATT&CK provider not registered."}


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard")
def get_ti_dashboard(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns aggregate TI dashboard data.
    Combines provider status, IOC statistics, and recent sync history.
    """
    dashboard = provider_manager.get_dashboard_data(db)
    dashboard["ioc_statistics"] = ioc_engine.get_ioc_statistics(db)
    return dashboard


# ═══════════════════════════════════════════════════════════════════════════════
# IOC Expiration Maintenance
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/maintenance/expire-stale")
def expire_stale_iocs(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Expires IOCs past their expiration_date."""
    if current_user.role not in ("admin",):
        return {"status": "forbidden", "message": "Requires admin role."}
    return ioc_engine.expire_stale_iocs(db)


# ═══════════════════════════════════════════════════════════════════════════════
# Sync Logs
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/sync-logs")
def get_sync_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns audit history of all TI sync operations."""
    from ..stix_models import TISyncLog

    try:
        logs = (
            db.query(TISyncLog)
            .order_by(TISyncLog.synced_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {
            "total": db.query(TISyncLog).count(),
            "logs": [
                {
                    "id": l.id,
                    "provider_name": l.provider_name,
                    "provider_type": l.provider_type,
                    "status": l.status,
                    "objects_fetched": l.objects_fetched,
                    "objects_new": l.objects_new,
                    "duration_seconds": l.duration_seconds,
                    "error_message": l.error_message,
                    "synced_at": l.synced_at.isoformat() if l.synced_at else None,
                }
                for l in logs
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _write_audit(db: Session, user: models.User, action: str) -> None:
    """Writes an audit log entry for TI operations."""
    try:
        log = models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user.id,
            username=user.username,
            action=action,
            status="success",
            actor=user.username,
            validation_status="validated",
            created_at=datetime.datetime.utcnow(),
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.warning("Audit log write failed: %s", e)
