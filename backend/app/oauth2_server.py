"""
OAuth2 Authorization Server & OpenID Connect (OIDC) Provider
Implements full OAuth2 flows for LEAtTrace
"""
import uuid
import datetime
import secrets
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from pydantic import BaseModel
import json

# ============= Enums =============

class GrantType(str, Enum):
    """OAuth2 grant types."""
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"
    CLIENT_CREDENTIALS = "client_credentials"
    IMPLICIT = "implicit"
    PASSWORD = "password"  # Resource Owner Password Credentials
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"

class ResponseType(str, Enum):
    """OAuth2 response types."""
    CODE = "code"
    TOKEN = "token"
    ID_TOKEN = "id_token"
    CODE_ID_TOKEN = "code id_token"
    CODE_TOKEN = "code token"
    ID_TOKEN_TOKEN = "id_token token"

class TokenType(str, Enum):
    """OAuth2 token types."""
    BEARER = "Bearer"
    MAC = "Mac"
    DPOP = "DPoP"  # Demonstrating Proof-of-Possession

class CodeChallengeMethod(str, Enum):
    """PKCE code challenge methods."""
    PLAIN = "plain"
    S256 = "S256"

# ============= Models =============

class OAuth2Client(BaseModel):
    """OAuth2 client application."""
    client_id: str
    client_name: str
    client_secret: Optional[str] = None  # None for public clients
    description: Optional[str] = None
    
    # Allowed flows
    allowed_grant_types: List[GrantType]
    allowed_response_types: List[ResponseType]
    
    # Redirect URIs
    redirect_uris: List[str]
    post_logout_redirect_uris: Optional[List[str]] = None
    
    # CORS and JWKS
    allowed_cors_origins: Optional[List[str]] = None
    jwks_uri: Optional[str] = None
    
    # Client metadata
    contacts: Optional[List[str]] = None
    logo_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    tos_uri: Optional[str] = None
    
    # Configuration
    token_endpoint_auth_method: str = "client_secret_basic"  # client_secret_basic, client_secret_post, private_key_jwt
    require_pkce: bool = False
    require_request_uri: bool = False
    
    # OIDC specific
    userinfo_signed_response_alg: Optional[str] = None
    id_token_signed_response_alg: str = "RS256"
    
    active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

class AuthorizationRequest(BaseModel):
    """OAuth2 Authorization Request."""
    request_id: str
    client_id: str
    response_type: ResponseType
    redirect_uri: str
    state: str  # CSRF protection
    scope: str  # Space-separated scopes
    
    # PKCE
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[CodeChallengeMethod] = None
    
    # OIDC specific
    nonce: Optional[str] = None
    display: Optional[str] = None
    prompt: Optional[str] = None
    max_age: Optional[int] = None
    ui_locales: Optional[str] = None
    id_token_hint: Optional[str] = None
    login_hint: Optional[str] = None
    acr_values: Optional[str] = None
    
    created_at: datetime.datetime
    expires_at: datetime.datetime
    approved_by_user: Optional[str] = None

class AuthorizationCode(BaseModel):
    """OAuth2 Authorization Code."""
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scope: str
    state: str
    nonce: Optional[str] = None
    
    # PKCE
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[CodeChallengeMethod] = None
    
    # Metadata
    created_at: datetime.datetime
    expires_at: datetime.datetime
    used: bool = False
    used_at: Optional[datetime.datetime] = None

class TokenRequest(BaseModel):
    """OAuth2 Token Request."""
    grant_type: GrantType
    client_id: str
    client_secret: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    refresh_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    code_verifier: Optional[str] = None
    scope: Optional[str] = None
    device_code: Optional[str] = None

class TokenResponse(BaseModel):
    """OAuth2 Token Response."""
    access_token: str
    token_type: TokenType = TokenType.BEARER
    expires_in: int  # Seconds
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None  # OIDC

class RefreshTokenRecord(BaseModel):
    """Refresh token record."""
    token: str
    client_id: str
    user_id: str
    scope: str
    issued_at: datetime.datetime
    expires_at: datetime.datetime
    rotation_count: int = 0
    last_used: Optional[datetime.datetime] = None
    revoked: bool = False

class OIDCUserInfo(BaseModel):
    """OIDC UserInfo response."""
    sub: str  # Subject (user ID)
    email: Optional[str] = None
    email_verified: bool = False
    phone_number: Optional[str] = None
    phone_number_verified: bool = False
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    middle_name: Optional[str] = None
    nickname: Optional[str] = None
    preferred_username: Optional[str] = None
    profile: Optional[str] = None
    picture: Optional[str] = None
    website: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    zoneinfo: Optional[str] = None
    locale: Optional[str] = None
    updated_at: Optional[datetime.datetime] = None
    
    # Custom claims
    department: Optional[str] = None
    clearance_level: Optional[int] = None
    roles: Optional[List[str]] = None

# ============= OAuth2 Server Engine =============

class OAuth2Server:
    """OAuth2 Authorization Server."""
    
    def __init__(self):
        """Initialize OAuth2 server."""
        self.clients: Dict[str, OAuth2Client] = {}
        self.authorization_requests: Dict[str, AuthorizationRequest] = {}
        self.authorization_codes: Dict[str, AuthorizationCode] = {}
        self.refresh_tokens: Dict[str, RefreshTokenRecord] = {}
        self.access_tokens: Dict[str, Dict[str, Any]] = {}
    
    def register_client(self, client: OAuth2Client) -> bool:
        """Register OAuth2 client application."""
        if client.client_id in self.clients:
            return False
        
        self.clients[client.client_id] = client
        return True
    
    def get_client(self, client_id: str) -> Optional[OAuth2Client]:
        """Get registered client."""
        return self.clients.get(client_id)
    
    def authenticate_client(
        self,
        client_id: str,
        client_secret: str
    ) -> Tuple[bool, Optional[str]]:
        """Authenticate OAuth2 client."""
        client = self.get_client(client_id)
        if not client:
            return False, "Invalid client ID"
        
        if not client.active:
            return False, "Client inactive"
        
        if client.client_secret != client_secret:
            return False, "Invalid client secret"
        
        return True, None
    
    def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> Tuple[bool, Optional[str]]:
        """Validate redirect URI for client."""
        client = self.get_client(client_id)
        if not client:
            return False, "Invalid client"
        
        if redirect_uri not in client.redirect_uris:
            return False, "Redirect URI not registered"
        
        return True, None
    
    def create_authorization_request(
        self,
        client_id: str,
        response_type: ResponseType,
        redirect_uri: str,
        state: str,
        scope: str,
        nonce: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[CodeChallengeMethod] = None,
        duration_seconds: int = 600
    ) -> Tuple[bool, Optional[AuthorizationRequest], Optional[str]]:
        """Create authorization request."""
        client = self.get_client(client_id)
        if not client:
            return False, None, "Invalid client"
        
        if response_type not in client.allowed_response_types:
            return False, None, "Response type not allowed"
        
        is_valid, reason = self.validate_redirect_uri(client_id, redirect_uri)
        if not is_valid:
            return False, None, reason
        
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        request_id = f"authreq_{uuid.uuid4().hex[:16]}"
        
        auth_request = AuthorizationRequest(
            request_id=request_id,
            client_id=client_id,
            response_type=response_type,
            redirect_uri=redirect_uri,
            state=state,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            nonce=nonce,
            created_at=now,
            expires_at=now + datetime.timedelta(seconds=duration_seconds)
        )
        
        self.authorization_requests[request_id] = auth_request
        return True, auth_request, None
    
    def get_authorization_request(self, request_id: str) -> Optional[AuthorizationRequest]:
        """Get authorization request."""
        auth_request = self.authorization_requests.get(request_id)
        if not auth_request:
            return None
        
        if datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) > auth_request.expires_at:
            return None  # Expired
        
        return auth_request
    
    def create_authorization_code(
        self,
        request: AuthorizationRequest,
        user_id: str,
        duration_seconds: int = 600
    ) -> AuthorizationCode:
        """Create authorization code after user approval."""
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        code_value = secrets.token_urlsafe(32)
        
        auth_code = AuthorizationCode(
            code=code_value,
            client_id=request.client_id,
            user_id=user_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            state=request.state,
            nonce=request.nonce,
            code_challenge=request.code_challenge,
            code_challenge_method=request.code_challenge_method,
            created_at=now,
            expires_at=now + datetime.timedelta(seconds=duration_seconds)
        )
        
        self.authorization_codes[code_value] = auth_code
        return auth_code
    
    def exchange_authorization_code(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Exchange authorization code for tokens."""
        auth_code = self.authorization_codes.get(code)
        if not auth_code:
            return False, None, "Invalid authorization code"
        
        if datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) > auth_code.expires_at:
            return False, None, "Authorization code expired"
        
        if auth_code.used:
            return False, None, "Authorization code already used"
        
        if auth_code.client_id != client_id:
            return False, None, "Client ID mismatch"
        
        if auth_code.redirect_uri != redirect_uri:
            return False, None, "Redirect URI mismatch"
        
        # Verify PKCE code verifier
        if auth_code.code_challenge:
            if not code_verifier:
                return False, None, "Code verifier required"
            
            if not self._verify_code_challenge(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
                return False, None, "Invalid code verifier"
        
        # Mark code as used
        auth_code.used = True
        auth_code.used_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        
        # Generate tokens
        access_token = self._generate_access_token(
            client_id=auth_code.client_id,
            user_id=auth_code.user_id,
            scope=auth_code.scope
        )
        
        refresh_token = self._generate_refresh_token(
            client_id=auth_code.client_id,
            user_id=auth_code.user_id,
            scope=auth_code.scope
        )
        
        id_token = None
        if "openid" in auth_code.scope:
            # Generate OIDC ID token
            id_token = self._generate_id_token(
                client_id=auth_code.client_id,
                user_id=auth_code.user_id,
                nonce=auth_code.nonce
            )
        
        return True, {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": auth_code.scope,
            "id_token": id_token
        }, None
    
    def refresh_access_token(
        self,
        refresh_token: str,
        client_id: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Refresh access token using refresh token."""
        refresh_record = self.refresh_tokens.get(refresh_token)
        if not refresh_record:
            return False, None, "Invalid refresh token"
        
        if datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) > refresh_record.expires_at:
            return False, None, "Refresh token expired"
        
        if refresh_record.revoked:
            return False, None, "Refresh token revoked"
        
        if refresh_record.client_id != client_id:
            return False, None, "Client ID mismatch"
        
        # Update last used and rotation count
        refresh_record.last_used = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        refresh_record.rotation_count += 1
        
        # Generate new tokens
        access_token = self._generate_access_token(
            client_id=refresh_record.client_id,
            user_id=refresh_record.user_id,
            scope=refresh_record.scope
        )
        
        # Optional: Rotate refresh token
        new_refresh_token = self._generate_refresh_token(
            client_id=refresh_record.client_id,
            user_id=refresh_record.user_id,
            scope=refresh_record.scope
        )
        
        return True, {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": new_refresh_token,
            "scope": refresh_record.scope
        }, None
    
    # ============= Token Generation =============
    
    @staticmethod
    def _generate_access_token(
        client_id: str,
        user_id: str,
        scope: str,
        duration_hours: int = 1
    ) -> str:
        """Generate access token."""
        token_id = f"tok_{uuid.uuid4().hex[:16]}"
        token_data = {
            "token_id": token_id,
            "client_id": client_id,
            "user_id": user_id,
            "scope": scope,
            "issued_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(),
            "expires_at": (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=duration_hours)).isoformat()
        }
        return json.dumps(token_data)
    
    @staticmethod
    def _generate_refresh_token(
        client_id: str,
        user_id: str,
        scope: str,
        duration_days: int = 7
    ) -> str:
        """Generate refresh token."""
        token_value = secrets.token_urlsafe(32)
        return token_value
    
    @staticmethod
    def _generate_id_token(
        client_id: str,
        user_id: str,
        nonce: Optional[str] = None
    ) -> str:
        """Generate OIDC ID token (JWT format)."""
        id_token_data = {
            "iss": "https://LEAtTrace.example.com",
            "sub": user_id,
            "aud": client_id,
            "nonce": nonce,
            "iat": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).timestamp(),
            "exp": (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=1)).timestamp()
        }
        return json.dumps(id_token_data)
    
    @staticmethod
    def _verify_code_challenge(
        code_verifier: str,
        code_challenge: str,
        method: Optional[CodeChallengeMethod] = None
    ) -> bool:
        """Verify PKCE code challenge."""
        if method == CodeChallengeMethod.PLAIN:
            return code_verifier == code_challenge
        
        elif method == CodeChallengeMethod.S256:
            # SHA256 hash of code verifier
            challenge_computed = hashlib.sha256(code_verifier.encode()).hexdigest()
            return challenge_computed == code_challenge
        
        return False
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""
        if refresh_token in self.refresh_tokens:
            self.refresh_tokens[refresh_token].revoked = True
            return True
        
        return False

# ============= OIDC Provider =============

class OIDCProvider:
    """OpenID Connect Provider."""
    
    def __init__(self, oauth2_server: OAuth2Server):
        """Initialize OIDC provider."""
        self.oauth2_server = oauth2_server
    
    def get_userinfo(self, user_id: str, access_token: str) -> Optional[OIDCUserInfo]:
        """Get user information for OIDC."""
        # Validate access token (simplified)
        try:
            token_data = json.loads(access_token)
            if token_data.get("user_id") != user_id:
                return None
        except Exception:
            return None
        
        # In production, fetch from database
        return OIDCUserInfo(
            sub=user_id,
            email=f"user{user_id}@LEAtTrace.gov.in",
            email_verified=True,
            name=f"User {user_id}",
            preferred_username=f"user{user_id}",
            updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
    
    def get_discovery_config(self, issuer_url: str) -> Dict[str, Any]:
        """Get OIDC discovery configuration."""
        return {
            "issuer": issuer_url,
            "authorization_endpoint": f"{issuer_url}/oauth/authorize",
            "token_endpoint": f"{issuer_url}/oauth/token",
            "userinfo_endpoint": f"{issuer_url}/oauth/userinfo",
            "jwks_uri": f"{issuer_url}/oauth/jwks",
            "scopes_supported": ["openid", "email", "profile"],
            "response_types_supported": ["code", "token", "id_token"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"]
        }
