from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any

# Auth Schemas
class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    user_id: str
    username: str
    role: str

# CPOS Schemas
class CPOSProcessRequest(BaseModel):
    input: str
    mode: str = "deep"

class CPOSProcessResponse(BaseModel):
    decision: str
    confidence: float
    reasoning_trace: List[str]
    governance: str = "passed"
    trace_id: str

# RIIL Schemas
class RIILIngestRequest(BaseModel):
    source: str
    data: dict

class RIILIngestResponse(BaseModel):
    status: str
    ingested_events_count: int

class RIILStateResponse(BaseModel):
    system_state: str
    external_sync: bool

# NGEL Schemas
class NGELEvaluateRequest(BaseModel):
    action: str
    risk_level: str

class NGELEvaluateResponse(BaseModel):
    allowed: bool
    reason: str

# QCAL Schemas
class QCALResolveRequest(BaseModel):
    inputs: List[str]

class QCALResolveResponse(BaseModel):
    selected: str
    probability: float
