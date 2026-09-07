"""
LEAtTrace IAM — Device Management API.

Enterprise device management endpoints: registration, trust,
fingerprinting, risk scoring, and forced logout.
"""

import uuid
import hashlib
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from .. import models, security
from ..device_manager import device_manager


router = APIRouter(prefix="/api/auth/devices", tags=["Device Management"])


def _generate_fingerprint(request: Request) -> str:
    """Generates a device fingerprint from request headers."""
    ua = request.headers.get("user-agent", "")
    accept_lang = request.headers.get("accept-language", "")
    accept_enc = request.headers.get("accept-encoding", "")
    ip = request.client.host if request.client else "127.0.0.1"
    raw = f"{ua}|{accept_lang}|{accept_enc}|{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.get("")
def list_devices(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all devices associated with the current user."""
    devices = db.query(models.TrustedDevice).filter(
        models.TrustedDevice.user_id == current_user.id
    ).order_by(models.TrustedDevice.last_used.desc()).all()

    return [
        {
            "id": d.id,
            "device_name": d.device_name,
            "os_name": d.os_name,
            "browser_name": d.browser_name,
            "ip_address": d.ip_address,
            "is_trusted": d.is_trusted,
            "last_used": d.last_used.isoformat() if d.last_used else None,
            "trust_expires_at": d.trust_expires_at.isoformat() if d.trust_expires_at else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in devices
    ]


@router.get("/current")
def get_current_device(
    request: Request,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """Returns device info for the current request."""
    ua = request.headers.get("user-agent", "Unknown")
    ip = request.client.host if request.client else "127.0.0.1"
    fingerprint = _generate_fingerprint(request)
    device_info = device_manager.parse_user_agent(ua)
    risk_score = device_manager.evaluate_device_risk(ip, ua, True)

    # Check if this device is trusted
    trusted = db.query(models.TrustedDevice).filter(
        models.TrustedDevice.user_id == current_user.id,
        models.TrustedDevice.device_fingerprint == fingerprint,
        models.TrustedDevice.is_trusted == True,
    ).first()

    return {
        "fingerprint": fingerprint,
        "os_name": device_info["os"],
        "browser_name": device_info["browser"],
        "ip_address": ip,
        "risk_score": risk_score,
        "is_trusted": trusted is not None,
    }


@router.post("/trust")
def trust_device(
    request: Request,
    device_name: str = Body("My Device", embed=True),
    trust_days: int = Body(90, embed=True),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """Registers the current device as trusted."""
    ua = request.headers.get("user-agent", "Unknown")
    ip = request.client.host if request.client else "127.0.0.1"
    fingerprint = _generate_fingerprint(request)
    device_info = device_manager.parse_user_agent(ua)

    # Check if already trusted
    existing = db.query(models.TrustedDevice).filter(
        models.TrustedDevice.user_id == current_user.id,
        models.TrustedDevice.device_fingerprint == fingerprint,
    ).first()

    if existing:
        existing.is_trusted = True
        existing.device_name = device_name
        existing.last_used = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        existing.trust_expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=trust_days)
        db.commit()
        return {"status": "device_trust_updated", "device_id": existing.id}

    new_device = models.TrustedDevice(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        device_fingerprint=fingerprint,
        device_name=device_name,
        os_name=device_info["os"],
        browser_name=device_info["browser"],
        ip_address=ip,
        is_trusted=True,
        trust_expires_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=trust_days),
    )
    db.add(new_device)
    db.commit()

    return {"status": "device_trusted", "device_id": new_device.id}


@router.post("/{device_id}/rename")
def rename_device(
    device_id: str,
    new_name: str = Body(..., embed=True),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """Renames a registered device."""
    device = db.query(models.TrustedDevice).filter(
        models.TrustedDevice.id == device_id,
        models.TrustedDevice.user_id == current_user.id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.device_name = new_name
    db.commit()
    return {"status": "renamed", "device_id": device_id, "new_name": new_name}


@router.delete("/{device_id}")
def remove_device(
    device_id: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a device and revokes its trust."""
    device = db.query(models.TrustedDevice).filter(
        models.TrustedDevice.id == device_id,
        models.TrustedDevice.user_id == current_user.id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.is_trusted = False
    db.commit()

    # Also revoke all sessions from this IP
    sessions = db.query(models.UserSession).filter(
        models.UserSession.user_id == current_user.id,
        models.UserSession.ip_address == device.ip_address,
        models.UserSession.is_active == True,
    ).all()
    for sess in sessions:
        sess.is_active = False
    db.commit()

    return {"status": "device_removed_and_sessions_revoked", "revoked_sessions": len(sessions)}
