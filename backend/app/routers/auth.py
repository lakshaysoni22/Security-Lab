import uuid
import datetime
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security
from ..event_broker import broker
from ..siem_exporter import log_security_event
from ..anomaly_detector import detect_login_brute_force

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Find user by username or email
    user = db.query(models.User).filter(
        (models.User.email == form_data.username) | 
        (models.User.username == form_data.username)
    ).first()

    ip_address = request.client.host if request.client else "127.0.0.1"

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        # Log to audit trail
        last_log = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).first()
        prev_hash = last_log.hash if last_log else "0"
        log_id = f"log_{uuid.uuid4().hex[:7]}"
        
        timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        timestamp_str = timestamp.isoformat()
        raw_str = f"{prev_hash}_{log_id}_Failed login attempt for account {form_data.username}_{timestamp_str}_failure"
        computed_hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

        audit_entry = models.AuditLog(
            id=log_id,
            user_id="anonymous",
            username=form_data.username,
            action=f"Failed login attempt for account {form_data.username}",
            ip_address=ip_address,
            status="failure",
            prev_hash=prev_hash,
            hash=computed_hash,
            timestamp=timestamp
        )
        db.add(audit_entry)
        db.commit()

        # Log to SIEM
        log_security_event(
            action=f"Failed login attempt on account: {form_data.username}",
            status="failure",
            username=form_data.username,
            ip_address=ip_address,
            severity="MEDIUM"
        )

        # Check anomaly
        await detect_login_brute_force(db, form_data.username, ip_address, broker)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if MFA is enabled
    if user.mfa_enabled:
        temp_token = security.create_access_token(
            data={"sub": user.id, "mfa_pending": True},
            expires_delta=datetime.timedelta(minutes=5)
        )
        return {
            "requires_mfa": True,
            "temp_token": temp_token,
            "user": user
        }

    # Generate full access & refresh tokens
    access_token = security.create_access_token(data={"sub": user.id})
    refresh_token = security.create_access_token(
        data={"sub": user.id, "refresh": True},
        expires_delta=datetime.timedelta(days=7)
    )

    # Create new session entry
    session_id = f"sess_{uuid.uuid4().hex[:7]}"
    user_agent = request.headers.get("user-agent", "Unknown Device")
    ip_address = request.client.host if request.client else "127.0.0.1"

    new_session = models.UserSession(
        id=session_id,
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
        expires_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=7)
    )
    db.add(new_session)
    
    # Update last login time
    user.last_login = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    
    # Audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=user.id,
        username=user.username,
        action="User logged in successfully (Non-MFA)",
        ip_address=ip_address,
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/mfa/setup", response_model=schemas.MFASetupOut)
def setup_mfa(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.mfa_secret:
        current_user.mfa_secret = security.generate_totp_secret()
        db.commit()

    totp_uri = security.get_totp_uri(current_user.mfa_secret, current_user.email)
    return {
        "secret": current_user.mfa_secret,
        "qr_code_uri": totp_uri
    }

@router.post("/mfa/verify")
def verify_mfa(
    request: Request,
    verify_req: schemas.MFAVerifyRequest,
    temp_token: str,
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate MFA session token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        from jose import jwt
        payload = jwt.decode(temp_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub")
        mfa_pending = payload.get("mfa_pending")
        if user_id is None or not mfa_pending:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise credentials_exception

    # Verify TOTP code
    is_valid = security.verify_totp_code(user.mfa_secret, verify_req.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 6-digit verification code"
        )

    # Enable user MFA status if not already set
    if not user.mfa_enabled:
        user.mfa_enabled = True
        db.commit()

    # Generate full access & refresh tokens
    access_token = security.create_access_token(data={"sub": user.id})
    refresh_token = security.create_access_token(
        data={"sub": user.id, "refresh": True},
        expires_delta=datetime.timedelta(days=7)
    )

    # Session Tracking
    session_id = f"sess_{uuid.uuid4().hex[:7]}"
    user_agent = request.headers.get("user-agent", "Unknown Device")
    ip_address = request.client.host if request.client else "127.0.0.1"

    new_session = models.UserSession(
        id=session_id,
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
        expires_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=7)
    )
    db.add(new_session)

    # Update last login
    user.last_login = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    # Log action
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=user.id,
        username=user.username,
        action="User logged in successfully via MFA TOTP",
        ip_address=ip_address,
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh", response_model=schemas.TokenRefreshResponse)
def refresh_token(
    refresh_req: schemas.TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        from jose import jwt
        payload = jwt.decode(refresh_req.refresh_token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub")
        is_refresh = payload.get("refresh")
        if user_id is None or not is_refresh:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    # Find active session with this refresh token (for token rotation check)
    session = db.query(models.UserSession).filter(
        models.UserSession.refresh_token == refresh_req.refresh_token,
        models.UserSession.is_active == True,
        models.UserSession.expires_at > datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    ).first()

    if not session:
        # Raise potential replay attack warning
        raise credentials_exception

    # Token Rotation: Invalidate previous session token
    session.is_active = False

    # Issue new access & refresh tokens
    new_access_token = security.create_access_token(data={"sub": user_id})
    new_refresh_token = security.create_access_token(
        data={"sub": user_id, "refresh": True},
        expires_delta=datetime.timedelta(days=7)
    )

    # Create rotated session entry
    new_session = models.UserSession(
        id=f"sess_{uuid.uuid4().hex[:7]}",
        user_id=user_id,
        refresh_token=new_refresh_token,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        is_active=True,
        expires_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=7)
    )
    db.add(new_session)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/sessions", response_model=list[schemas.UserSessionOut])
def get_active_sessions(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(models.UserSession).filter(
        models.UserSession.user_id == current_user.id,
        models.UserSession.is_active == True
    ).all()
    return sessions

@router.post("/sessions/revoke/{session_id}")
def revoke_session(
    session_id: str,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(models.UserSession).filter(
        models.UserSession.id == session_id,
        models.UserSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session.is_active = False
    
    # Audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Revoked active device session: {session_id}",
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    return {"detail": "Session revoked successfully"}

@router.post("/oauth/{provider}")
def oauth_login(
    provider: str,
    request: Request,
    auth_code: str,
    db: Session = Depends(get_db)
):
    if provider not in ["google", "microsoft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth2 provider. Supported: google, microsoft"
        )

    # Simulated OAuth2 resource exchange (fetching user details from code)
    simulated_email = f"officer.{auth_code.lower()[:5]}@cybercrime.gov.in"
    simulated_username = f"Officer {auth_code.capitalize()[:5]}"

    # Find or create user
    user = db.query(models.User).filter(models.User.email == simulated_email).first()
    if not user:
        user = models.User(
            id=f"usr_{uuid.uuid4().hex[:7]}",
            email=simulated_email,
            username=simulated_username,
            hashed_password=security.get_password_hash("OAuthSecureDefaultPass!2026"),
            role="investigator",
            is_active=True,
            mfa_enabled=False,
            oauth_provider=provider,
            oauth_id=f"oauth_{uuid.uuid4().hex[:7]}",
            department="Cyber Crime Cell"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate full access & refresh tokens
    access_token = security.create_access_token(data={"sub": user.id})
    refresh_token = security.create_access_token(
        data={"sub": user.id, "refresh": True},
        expires_delta=datetime.timedelta(days=7)
    )

    # Store Session
    session_id = f"sess_{uuid.uuid4().hex[:7]}"
    user_agent = request.headers.get("user-agent", "Unknown Device")
    ip_address = request.client.host if request.client else "127.0.0.1"

    new_session = models.UserSession(
        id=session_id,
        user_id=user.id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
        expires_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=7)
    )
    db.add(new_session)

    # Audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=user.id,
        username=user.username,
        action=f"User authenticated via OAuth2 ({provider.capitalize()})",
        ip_address=ip_address,
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user
