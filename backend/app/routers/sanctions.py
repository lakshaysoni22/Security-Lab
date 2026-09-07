"""
LEATrace Sanctions Router — Production.

REST endpoints for the Sanctions Intelligence Platform:
- Provider management (status, toggle, health)
- Manual and automated sync with integrity reports
- Wallet, entity, transaction, and batch screening
- Version history and change tracking
- Screening audit logs
- Background scheduler status

PRODUCTION INVARIANTS:
- Never returns hardcoded sanctioned entities.
- All data sourced from the normalized sanctions database.
- Every screening event produces an immutable audit log.
- If DB is empty, returns structured guidance — not fake data.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, security
from ..feed_scheduler import feed_scheduler
from ..threat_database import threat_db
from ..sanctions_screening_engine import sanctions_screening_engine
from ..providers.sanctions_provider_manager import sanctions_provider_manager

logger = logging.getLogger("leatrace.routers.sanctions")

router = APIRouter(prefix="/api/sanctions", tags=["Sanctions Intelligence"])


# ═══════════════════════════════════════════════════════════════════════════════
# Request Models
# ═══════════════════════════════════════════════════════════════════════════════

class WalletScreenRequest(BaseModel):
    address: str
    reason_context: Optional[str] = None


class EntityScreenRequest(BaseModel):
    name: str
    fuzzy_threshold: float = 0.8
    reason_context: Optional[str] = None


class TransactionScreenRequest(BaseModel):
    tx_hash: str
    sender: str
    receiver: str
    reason_context: Optional[str] = None


class BatchScreenRequest(BaseModel):
    addresses: List[str]
    reason_context: Optional[str] = None


class ProviderToggleRequest(BaseModel):
    enabled: bool


# ═══════════════════════════════════════════════════════════════════════════════
# Provider Management
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/status")
def get_sanctions_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """
    Returns sanctions provider configuration, last sync status,
    and screening statistics.
    """
    feed_status = feed_scheduler.get_status(db=db)
    screening_stats = sanctions_screening_engine.get_screening_stats(db)
    provider_statuses = sanctions_provider_manager.get_all_statuses()

    return {
        "feed_status": feed_status,
        "screening_stats": screening_stats,
        "providers": provider_statuses,
    }


@router.get("/providers")
def list_providers(
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Lists all registered sanctions providers with health and sync stats."""
    return sanctions_provider_manager.get_all_statuses()


@router.get("/providers/health")
def health_check_providers(
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Performs a live health check on all sanctions data providers."""
    return sanctions_provider_manager.health_check_all()


@router.post("/providers/{provider_id}/toggle")
def toggle_provider(
    provider_id: str,
    body: ProviderToggleRequest,
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Enables or disables a specific sanctions provider. Supervisor/Admin only."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    logger.info("Provider '%s' toggle to %s by %s", provider_id, body.enabled, current_user.username)
    return sanctions_provider_manager.toggle_provider(provider_id, body.enabled)


# ═══════════════════════════════════════════════════════════════════════════════
# Sync Operations
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/sync")
def trigger_sanctions_sync(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """
    Triggers a live download and ingestion of all configured sanctions sources.
    Admin or supervisor role required.
    Downloads real OFAC SDN XML, EU Consolidated XML, and UN Consolidated XML.
    """
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    logger.info("Sanctions sync triggered by %s", current_user.username)
    return feed_scheduler.run_daily_sync(db=db)


@router.post("/sync/{provider_id}")
def trigger_provider_sync(
    provider_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Triggers sync for a specific sanctions provider. Supervisor/Admin only."""
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    logger.info("Provider sync '%s' triggered by %s", provider_id, current_user.username)
    return sanctions_provider_manager.sync_provider(provider_id, db)


@router.get("/scheduler")
def get_scheduler_status(
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Returns background scheduler status and configuration."""
    from ..sanctions_scheduler import sanctions_scheduler
    return sanctions_scheduler.get_scheduler_status()


# ═══════════════════════════════════════════════════════════════════════════════
# Screening Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/check/{address}")
def check_address_sanctions(
    address: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """
    Checks a crypto wallet address against the local sanctions DB.
    Also checks STIX indicators from TAXII sync.

    Returns match details if found, clean result if not found.
    Never fabricates — if DB is empty, directs user to run /sync first.
    """
    # Screen via new engine
    screen_result = sanctions_screening_engine.screen_wallet(
        address, db, checked_by=current_user.username,
    )

    # Also check STIX indicators (legacy compatibility)
    stix_hit = threat_db.check_stix_indicator(address, db=db)

    # Get DB entry count for context
    from ..sanctions_models import SanctionsListEntity
    total_entities = db.query(SanctionsListEntity).filter(
        SanctionsListEntity.status == "active",
        SanctionsListEntity.is_deleted == False,  # noqa: E712
    ).count()

    result: Dict[str, Any] = {
        "query_address": address,
        "sanctioned": screen_result["matched"],
        "screening_result": screen_result,
        "stix_flagged": stix_hit is not None,
        "stix_detail": stix_hit,
        "database_entities": total_entities,
    }

    if total_entities == 0:
        result["notice"] = (
            "Sanctions database is empty. "
            "Configure providers and run POST /api/sanctions/sync to populate."
        )

    return result


@router.post("/screen/wallet")
def screen_wallet(
    body: WalletScreenRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Screens a wallet address against the sanctions database with full audit trail."""
    return sanctions_screening_engine.screen_wallet(
        body.address, db,
        checked_by=current_user.username,
        reason_context=body.reason_context,
    )


@router.post("/screen/entity")
def screen_entity(
    body: EntityScreenRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Screens an entity name against the sanctions database with fuzzy matching."""
    return sanctions_screening_engine.screen_entity(
        body.name, db,
        checked_by=current_user.username,
        reason_context=body.reason_context,
        fuzzy_threshold=body.fuzzy_threshold,
    )


@router.post("/screen/transaction")
def screen_transaction(
    body: TransactionScreenRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Screens a blockchain transaction by checking both sender and receiver."""
    return sanctions_screening_engine.screen_transaction(
        body.tx_hash, body.sender, body.receiver, db,
        checked_by=current_user.username,
        reason_context=body.reason_context,
    )


@router.post("/screen/batch")
def screen_batch(
    body: BatchScreenRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Screens multiple wallet addresses in a single request."""
    if len(body.addresses) > 1000:
        return {"status": "error", "message": "Maximum 1000 addresses per batch."}
    return sanctions_screening_engine.screen_batch(
        body.addresses, db,
        checked_by=current_user.username,
        reason_context=body.reason_context,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Data Browsing & History
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/entries")
def list_sanctions_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    provider_id: Optional[str] = Query(None, description="Filter by provider"),
    entity_type: Optional[str] = Query(None, description="individual|organization|vessel"),
    status: Optional[str] = Query(None, description="active|revoked|expired"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Paginated list of sanctioned entities from the normalized database."""
    from ..sanctions_models import SanctionsListEntity

    query = db.query(SanctionsListEntity).filter(
        SanctionsListEntity.is_deleted == False,  # noqa: E712
    )

    if provider_id:
        query = query.filter(SanctionsListEntity.provider_id == provider_id)
    if entity_type:
        query = query.filter(SanctionsListEntity.entity_type == entity_type)
    if status:
        query = query.filter(SanctionsListEntity.status == status)
    else:
        query = query.filter(SanctionsListEntity.status == "active")

    total = query.count()
    entries = query.order_by(SanctionsListEntity.name).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "entries": [
            {
                "id": e.id,
                "entity_uid": e.entity_uid,
                "provider_id": e.provider_id,
                "name": e.name,
                "entity_type": e.entity_type,
                "program": e.program,
                "status": e.status,
                "wallets": [
                    {"address": w.address, "currency": w.currency}
                    for w in e.wallets if not w.is_deleted
                ],
                "aliases": [
                    {"alias_name": a.alias_name, "alias_type": a.alias_type}
                    for a in e.aliases
                ],
                "countries": [
                    {"country_code": c.country_code, "country_name": c.country_name}
                    for c in e.countries
                ],
                "created_at": e.created_at.isoformat() + "Z" if e.created_at else None,
                "updated_at": e.updated_at.isoformat() + "Z" if e.updated_at else None,
            }
            for e in entries
        ],
    }


@router.get("/versions")
def list_versions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    provider_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Paginated version history of sanctions data syncs."""
    from ..sanctions_models import SanctionsVersionHistory

    query = db.query(SanctionsVersionHistory)
    if provider_id:
        query = query.filter(SanctionsVersionHistory.provider_id == provider_id)

    total = query.count()
    versions = (
        query.order_by(SanctionsVersionHistory.synced_at.desc())
        .offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "versions": [
            {
                "id": v.id,
                "provider_id": v.provider_id,
                "version": v.version,
                "checksum": v.checksum,
                "status": v.status,
                "entities_count": v.entities_count,
                "wallets_count": v.wallets_count,
                "delta_added": v.delta_added,
                "delta_updated": v.delta_updated,
                "delta_removed": v.delta_removed,
                "duration_seconds": v.duration_seconds,
                "synced_at": v.synced_at.isoformat() + "Z" if v.synced_at else None,
            }
            for v in versions
        ],
    }


@router.get("/changes")
def list_changes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    provider_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None, description="added|modified|removed"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Paginated change history for sanctions data mutations."""
    from ..sanctions_models import SanctionsChangeHistory

    query = db.query(SanctionsChangeHistory)
    if provider_id:
        query = query.filter(SanctionsChangeHistory.provider_id == provider_id)
    if action:
        query = query.filter(SanctionsChangeHistory.action == action)

    total = query.count()
    changes = (
        query.order_by(SanctionsChangeHistory.changed_at.desc())
        .offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "changes": [
            {
                "id": c.id,
                "version_id": c.version_id,
                "entity_uid": c.entity_uid,
                "provider_id": c.provider_id,
                "action": c.action,
                "field_changed": c.field_changed,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "changed_at": c.changed_at.isoformat() + "Z" if c.changed_at else None,
            }
            for c in changes
        ],
    }


@router.get("/integrity-reports")
def list_integrity_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    provider_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Paginated list of sync integrity validation reports."""
    from ..sanctions_models import SanctionsSyncIntegrityReport

    query = db.query(SanctionsSyncIntegrityReport)
    if provider_id:
        query = query.filter(SanctionsSyncIntegrityReport.provider_id == provider_id)

    total = query.count()
    reports = (
        query.order_by(SanctionsSyncIntegrityReport.validated_at.desc())
        .offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "reports": [
            {
                "id": r.id,
                "version_id": r.version_id,
                "provider_id": r.provider_id,
                "checksum": r.checksum,
                "is_valid": r.is_valid,
                "total_entities": r.total_entities,
                "unique_entities": r.unique_entities,
                "duplicate_uids": r.duplicate_uids,
                "total_wallets": r.total_wallets,
                "issues": r.issues_json,
                "download_size_bytes": r.download_size_bytes,
                "validated_at": r.validated_at.isoformat() + "Z" if r.validated_at else None,
            }
            for r in reports
        ],
    }


@router.get("/screening-logs")
def list_screening_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    query_type: Optional[str] = Query(None, description="wallet|entity_name|transaction|batch"),
    matched_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Paginated, immutable audit log of all sanctions screening events."""
    from ..sanctions_models import SanctionsScreeningLog

    query = db.query(SanctionsScreeningLog)
    if query_type:
        query = query.filter(SanctionsScreeningLog.query_type == query_type)
    if matched_only:
        query = query.filter(SanctionsScreeningLog.matched == True)  # noqa: E712

    total = query.count()
    logs = (
        query.order_by(SanctionsScreeningLog.checked_at.desc())
        .offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "logs": [
            {
                "id": l.id,
                "query_type": l.query_type,
                "query_value": l.query_value,
                "matched": l.matched,
                "match_score": l.match_score,
                "matched_entity_name": l.matched_entity_name,
                "matched_programs": l.matched_programs,
                "provider_id": l.provider_id,
                "checked_by": l.checked_by,
                "reason_context": l.reason_context,
                "response_time_ms": l.response_time_ms,
                "checked_at": l.checked_at.isoformat() + "Z" if l.checked_at else None,
            }
            for l in logs
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy Compatibility (Sync Logs from old SanctionsSyncLog table)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/sync-logs")
def get_sync_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user),
) -> Dict[str, Any]:
    """Returns audit history of all sanctions sync runs (legacy table)."""
    try:
        logs = (
            db.query(models.SanctionsSyncLog)
            .order_by(models.SanctionsSyncLog.synced_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {
            "total": db.query(models.SanctionsSyncLog).count(),
            "logs": [
                {
                    "id":             l.id,
                    "provider":       l.provider,
                    "status":         l.status,
                    "entries_added":  l.entries_added,
                    "entries_updated": l.entries_updated,
                    "file_hash":      l.file_hash,
                    "error_message":  l.error_message,
                    "synced_at":      l.synced_at.isoformat() + "Z" if l.synced_at else None,
                }
                for l in logs
            ],
        }
    except Exception:
        return {"total": 0, "logs": [], "note": "Legacy sync log table not available."}
