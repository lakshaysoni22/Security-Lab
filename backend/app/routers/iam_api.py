from fastapi import APIRouter, HTTPException, Query, Header, Depends, Body
from typing import List, Dict, Any, Optional
from ..oauth_server import oauth_server
from ..oidc_provider import oidc_provider
from ..refresh_service import refresh_service
from ..device_manager import device_manager
from ..session_manager import session_manager
from ..rbac_engine import rbac_engine
from ..abac_engine import abac_engine

router = APIRouter(tags=["IAM & Authentication Services"])

# Public JWKS Mock Key
JWK_KEY = {
    "keys": [
        {
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": "LEAtTrace-key-v1",
            "n": "u1W1x_x_mock_modulus_key_value_100",
            "e": "AQAB"
        }
    ]
}

@router.get("/.well-known/openid-configuration")
def get_oidc_config():
    return oidc_provider.get_discovery_document()

@router.get("/jwks.json")
def get_jwks():
    return JWK_KEY

@router.post("/oauth/token")
def issue_oauth_token(
    grant_type: str = Body(...),
    code: Optional[str] = Body(None),
    client_id: str = Body(...),
    client_secret: Optional[str] = Body(None),
    code_verifier: Optional[str] = Body(None),
    refresh_token: Optional[str] = Body(None)
):
    if grant_type == "authorization_code":
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        # Validate auth code and PKCE verifier
        is_valid = oauth_server.validate_auth_code(code, client_id, code_verifier)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid authorization code or PKCE verification failed")
            
        # Issue initial tokens
        family_id, new_refresh = refresh_service.create_family()
        return {
            "access_token": "acc_initial_token_jwt",
            "id_token": "id_token_jwt_placeholder",
            "refresh_token": new_refresh,
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Missing refresh token")
        try:
            new_ref, new_acc = refresh_service.rotate_token(refresh_token)
            return {
                "access_token": new_acc,
                "refresh_token": new_ref,
                "expires_in": 3600,
                "token_type": "Bearer"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    elif grant_type == "client_credentials":
        return {
            "access_token": "client_credentials_access_token_jwt",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
    raise HTTPException(status_code=400, detail="Unsupported grant type")

@router.get("/userinfo")
def get_userinfo(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return oidc_provider.generate_id_token("user_101", "lakshaysoni@cybercrime.gov.in", "investigator", "Cybercrime Unit")

@router.get("/auth/device")
def get_device_history(user_agent: Optional[str] = Header(None)):
    ua = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
    device_details = device_manager.parse_user_agent(ua)
    risk_score = device_manager.evaluate_device_risk("192.168.1.5", ua, True)
    
    return {
        "device_details": device_details,
        "ip_address": "192.168.1.5",
        "risk_score": risk_score,
        "is_trusted": True
    }

@router.post("/auth/session/revoke")
def revoke_session(session_id: str = Body(..., embed=True)):
    success = session_manager.terminate_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "revoked", "session_id": session_id}

@router.post("/auth/policies/evaluate")
def evaluate_abac_policy(
    user_clearance: int = Body(...),
    resource_clearance: int = Body(...),
    department: str = Body(...),
    restriction: Optional[str] = Body(None)
):
    user_attrs = {"clearance_level": user_clearance, "department": department, "role": "investigator"}
    res_attrs = {"clearance_required": resource_clearance, "department_restriction": restriction}
    env_attrs = {"current_hour": 14}
    
    allowed = abac_engine.evaluate_policy(user_attrs, res_attrs, env_attrs)
    return {"allowed": allowed}
