from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime

# Auth Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: str
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: UserOut

# Case Schemas
class CaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "open"
    notes: Optional[str] = None

class CaseCreate(CaseBase):
    case_number: Optional[str] = None

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    closed_at: Optional[datetime] = None

class WalletBase(BaseModel):
    address: str
    chain: str
    label: Optional[str] = None
    tags: Optional[str] = None
    risk_score: int = 0
    is_contract: bool = False

class WalletCreate(WalletBase):
    pass

class WalletOut(WalletBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str

class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    filename: str
    file_hash: str
    file_size: int
    uploaded_by: str
    upload_time: datetime
    description: Optional[str] = None

class CaseOut(CaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_number: str
    investigator_id: str
    investigator_name: Optional[str] = None
    department: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    wallets: List[WalletOut] = []
    evidence: List[EvidenceOut] = []

# Watchlist Schemas
class WatchlistBase(BaseModel):
    address: str
    chain: str
    alias: Optional[str] = None
    risk_score: int = 0
    status: str = "Monitored"

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistOut(WatchlistBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime

# Alert Schemas
class AlertBase(BaseModel):
    chain: str
    address: str
    alias: Optional[str] = None
    type: str
    threshold: float
    severity: str = "medium"

class AlertCreate(AlertBase):
    pass

class AlertOut(AlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime
    message: Optional[str] = None
    is_read: bool

# AuditLog Schema
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    username: str
    action: str
    ip_address: Optional[str] = None
    timestamp: datetime
    status: str
    actor: str
    decision_source: Optional[str] = None
    execution_result: Optional[str] = None
    validation_status: str

# AI Chat Schemas
class AIChatRequest(BaseModel):
    message: str
    context_case_id: Optional[str] = None
    context_address: Optional[str] = None

class AIChatResponse(BaseModel):
    response: str

class FAIISTriggerRequest(BaseModel):
    target_address: str
    risk_score: int
    anomaly_details: str

# --- Dynamic Security & Forensic Schemas ---

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class MFASetupOut(BaseModel):
    secret: str
    qr_code_uri: str

class MFAVerifyRequest(BaseModel):
    code: str

class LoginMFAStatus(BaseModel):
    requires_mfa: bool
    temp_token: Optional[str] = None
    user: Optional[UserOut] = None

class UserSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    created_at: datetime
    expires_at: datetime

class ChainOfCustodyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evidence_id: str
    action: str
    performed_by: str
    recipient: Optional[str] = None
    timestamp: datetime
    notes: Optional[str] = None
    prev_hash: Optional[str] = None
    hash_signature: Optional[str] = None

class EvidenceSignatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    evidence_id: str
    signer_name: str
    signature: str
    timestamp: datetime
    public_key_pem: str

class LedgerVerificationOut(BaseModel):
    is_valid: bool
    total_entries: int
    tampered_indices: List[int]
    message: str
