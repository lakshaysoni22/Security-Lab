"""
LEATrace TAXII Router — Production.

REST endpoints for TAXII 2.1 server management and threat intelligence synchronization.

PRODUCTION INVARIANTS:
- All endpoints return real data or structured "not_configured" status.
- No hardcoded threat intel. No fabricated indicators.
- Sync operations write to DB and audit log.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, security
from ..taxii_client import taxii_client, NOT_CONFIGURED, TAXIIError
from ..stix_engine import stix_engine

logger = logging.getLogger("leatrace.routers.taxii")

router = APIRouter(prefix="/api/taxii", tags=["TAXII 2.1 / Threat Intelligence"])


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/status")
def get_taxii_status(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns TAXII server configuration and connectivity health.
    Safe to call frequently — no sync side effects.
    """
    health = taxii_client.health_check()

    # Append last sync stats from DB
    last_sync = (
        db.query(models.TaxiiSyncState)
        .order_by(models.TaxiiSyncState.last_synced_at.desc())
        .first()
    )
    health["last_sync"] = {
        "collection_id":   last_sync.collection_id if last_sync else None,
        "last_synced_at":  last_sync.last_synced_at.isoformat() + "Z" if last_sync and last_sync.last_synced_at else None,
        "objects_synced":  last_sync.objects_synced if last_sync else 0,
        "error_count":     last_sync.error_count if last_sync else 0,
    }
    return health


@router.get("/collections")
def list_taxii_collections(
    current_user: models.User = Depends(security.get_current_user),
) -> List[Dict[str, Any]]:
    """
    Lists available collections on the configured TAXII server.
    Returns structured not_configured if server not set.
    """
    if not taxii_client.is_configured():
        return [NOT_CONFIGURED]
    return taxii_client.list_collections()


@router.post("/sync")
def trigger_taxii_sync(
    collection_id: str = Query(..., description="TAXII collection ID to synchronize"),
    delta: bool = Query(True, description="Use delta sync from last sync timestamp"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Triggers a TAXII collection sync — runs inline (not background) to keep
    the response informative. Use delta=true for incremental sync.

    Returns sync summary with object counts and any errors.
    Requires supervisor role or above.
    """
    if current_user.role not in ("admin", "supervisor"):
        return {"status": "forbidden", "message": "Requires supervisor or admin role."}

    if not taxii_client.is_configured():
        return NOT_CONFIGURED

    # Resolve added_after from last sync state
    added_after: Optional[str] = None
    if delta:
        state = (
            db.query(models.TaxiiSyncState)
            .filter(models.TaxiiSyncState.collection_id == collection_id)
            .first()
        )
        if state and state.last_synced_at:
            added_after = state.last_synced_at.isoformat() + "Z"

    logger.info("TAXII sync triggered: collection=%s delta=%s added_after=%s by=%s",
                collection_id, delta, added_after, current_user.username)

    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    synced_count = 0
    error_count = 0
    wallet_hits = 0

    try:
        objects = taxii_client.sync_collection_objects(
            collection_id=collection_id,
            added_after=added_after,
        )

        for obj in objects:
            if isinstance(obj, dict) and obj.get("status") in ("not_configured", "error"):
                return obj  # Propagate config/error status

            try:
                stix_engine.validate_object(obj)
            except Exception as ve:
                logger.warning("Invalid STIX object skipped: %s", ve)
                error_count += 1
                continue

            # Persist Indicator objects to StixIndicator table
            if obj.get("type") == "indicator":
                _upsert_stix_indicator(db, obj, collection_id)
                # Extract wallet addresses
                addrs = stix_engine.extract_wallet_addresses(obj)
                wallet_hits += len(addrs)

            synced_count += 1

        db.commit()

    except Exception as e:
        logger.error("TAXII sync error: %s", e)
        error_count += 1

    # Update sync state
    _update_sync_state(db, collection_id, now, synced_count, error_count)

    # Audit log
    _write_audit(db, current_user, f"TAXII_SYNC: collection={collection_id} objects={synced_count} wallets={wallet_hits}", now)

    return {
        "status": "completed",
        "collection_id": collection_id,
        "objects_synced": synced_count,
        "wallet_addresses_extracted": wallet_hits,
        "error_count": error_count,
        "delta_sync": delta,
        "added_after": added_after,
        "synced_at": now.isoformat() + "Z",
    }


@router.get("/indicators")
def list_stix_indicators(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    collection_id: Optional[str] = Query(None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns paginated STIX Indicator objects from the local DB.
    These are populated by sync operations from the configured TAXII server.
    """
    query = db.query(models.StixIndicator)
    if collection_id:
        query = query.filter(models.StixIndicator.collection_id == collection_id)

    total = query.count()
    items = query.order_by(models.StixIndicator.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "indicators": [
            {
                "id": i.id,
                "stix_id": i.stix_id,
                "name": i.name,
                "pattern": i.pattern,
                "pattern_type": i.pattern_type,
                "valid_from": i.valid_from.isoformat() + "Z" if i.valid_from else None,
                "collection_id": i.collection_id,
                "confidence": i.confidence,
                "synced_at": i.created_at.isoformat() + "Z" if i.created_at else None,
            }
            for i in items
        ],
        "data_source": "database" if total > 0 else "empty — run POST /api/taxii/sync to populate",
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _upsert_stix_indicator(db: Session, obj: Dict[str, Any], collection_id: str) -> None:
    """Insert or update a STIX Indicator in the database."""
    stix_id = obj.get("id")
    existing = db.query(models.StixIndicator).filter(models.StixIndicator.stix_id == stix_id).first()

    valid_from = None
    if obj.get("valid_from"):
        try:
            valid_from = datetime.datetime.fromisoformat(obj["valid_from"].replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            pass

    if existing:
        existing.name = obj.get("name", existing.name)
        existing.pattern = obj.get("pattern", existing.pattern)
        existing.confidence = obj.get("confidence")
        existing.valid_from = valid_from
        existing.updated_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    else:
        indicator = models.StixIndicator(
            id=str(uuid.uuid4()),
            stix_id=stix_id,
            name=obj.get("name"),
            pattern=obj.get("pattern"),
            pattern_type=obj.get("pattern_type", "stix"),
            valid_from=valid_from,
            collection_id=collection_id,
            confidence=obj.get("confidence"),
            raw_json=str(obj),
        )
        db.add(indicator)


def _update_sync_state(db: Session, collection_id: str, now: datetime.datetime, synced: int, errors: int) -> None:
    """Upserts TAXII sync state for a collection."""
    state = db.query(models.TaxiiSyncState).filter(models.TaxiiSyncState.collection_id == collection_id).first()
    if state:
        state.last_synced_at = now
        state.objects_synced += synced
        state.error_count += errors
    else:
        state = models.TaxiiSyncState(
            id=str(uuid.uuid4()),
            collection_id=collection_id,
            last_synced_at=now,
            objects_synced=synced,
            error_count=errors,
        )
        db.add(state)
    db.commit()


def _write_audit(db: Session, user: models.User, action: str, now: datetime.datetime) -> None:
    """Writes an audit log entry for TAXII operations."""
    try:
        log = models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user.id,
            username=user.username,
            action=action,
            status="success",
            actor=user.username,
            validation_status="validated",
            created_at=now,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.warning("Failed to write audit log: %s", e)
