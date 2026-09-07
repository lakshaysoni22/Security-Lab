import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas, security

router = APIRouter(prefix="/api/audit", tags=["Compliance Audit"])

@router.get("/logs", response_model=List[schemas.AuditLogOut])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.RoleChecker(["admin", "supervisor", "auditor"]))
):
    return db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).all()

@router.get("/verify", response_model=schemas.LedgerVerificationOut)
def verify_audit_ledger(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.RoleChecker(["admin", "auditor"]))
):
    # Fetch logs in chronological order to traverse the hash chain
    logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.asc()).all()

    tampered_indices = []
    prev_hash = "0"

    for idx, log in enumerate(logs):
        # 1. Verify prev_hash pointer matching
        if log.prev_hash != prev_hash:
            tampered_indices.append(idx)
            # Synchronize pointer to continue checking next links
            prev_hash = log.hash
            continue

        # 2. Recompute log hash signature
        timestamp_str = log.timestamp.isoformat() if log.timestamp else ""
        raw_str = f"{prev_hash}_{log.id}_{log.action}_{timestamp_str}_{log.status}"
        computed_hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

        if log.hash != computed_hash:
            tampered_indices.append(idx)
            # Synchronize pointer to continue checking next links
            prev_hash = log.hash
            continue

        # Move to next block pointer
        prev_hash = log.hash

    is_valid = len(tampered_indices) == 0
    message = "Audit log ledger is fully intact and verified." if is_valid else f"Tampering detected! Chain broken at {len(tampered_indices)} entry/entries."

    return {
        "is_valid": is_valid,
        "total_entries": len(logs),
        "tampered_indices": tampered_indices,
        "message": message
    }
