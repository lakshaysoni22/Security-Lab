from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any
from ..totp_service import totp_service
from ..policy_engine import policy_engine

router = APIRouter(prefix="/api/auth", tags=["Identity & Security Operations"])

# Local mock storage for keys/sessions
ENROLLED_SECRETS = {} # username -> base32_secret
ACTIVE_SESSIONS = [
    {"session_id": "sess_001", "device_name": "Google Chrome (Windows)", "ip_address": "192.168.1.45", "last_active": "2026-06-29T12:00:00Z"},
    {"session_id": "sess_002", "device_name": "Mozilla Firefox (Mac OS)", "ip_address": "192.168.5.12", "last_active": "2026-06-29T11:45:00Z"}
]

@router.post("/mfa/enroll")
def enroll_mfa(username: str = Body(..., embed=True)):
    enrollment = totp_service.generate_totp_secret()
    ENROLLED_SECRETS[username] = enrollment["secret"]
    backup_codes = totp_service.generate_backup_codes()
    
    return {
        "status": "enrolling",
        "secret": enrollment["secret"],
        "registration_uri": enrollment["registration_uri"],
        "backup_recovery_codes": backup_codes
    }

@router.post("/mfa/verify")
def verify_mfa(
    username: str = Body(...),
    code: str = Body(...)
):
    if policy_engine.is_account_locked(username):
        raise HTTPException(status_code=403, detail="Account locked due to brute force protection. Try again in 10 minutes.")
        
    secret = ENROLLED_SECRETS.get(username)
    if not secret:
        raise HTTPException(status_code=404, detail="MFA enrollment not found for user")
        
    is_valid = totp_service.verify_totp_token(secret, code)
    if is_valid:
        policy_engine.reset_failed_logins(username)
        return {"status": "verified", "token_type": "bearer", "access_token": "mock-short-access-token-jwt"}
    else:
        policy_engine.record_failed_login(username)
        raise HTTPException(status_code=401, detail="Invalid verification code")

@router.post("/refresh")
def rotate_refresh_token(refresh_token: str = Body(..., embed=True)):
    # Simulates Refresh Token Rotation (RTR)
    return {
        "access_token": "new-short-access-token-jwt",
        "refresh_token": "rotated-refresh-token-jwt"
    }

@router.get("/sessions")
def get_active_sessions():
    return ACTIVE_SESSIONS

@router.post("/sessions/revoke")
def revoke_active_session(session_id: str = Body(..., embed=True)):
    global ACTIVE_SESSIONS
    original_len = len(ACTIVE_SESSIONS)
    ACTIVE_SESSIONS = [s for s in ACTIVE_SESSIONS if s["session_id"] != session_id]
    
    if len(ACTIVE_SESSIONS) == original_len:
        raise HTTPException(status_code=404, detail="Session token not found")
    return {"status": "revoked", "session_id": session_id}
