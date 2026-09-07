import time
import uuid
from typing import Dict, Any

class OIDCProvider:
    def get_discovery_document(self, issuer_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Returns standard OpenID Connect Provider Discovery metadata."""
        return {
            "issuer": issuer_url,
            "authorization_endpoint": f"{issuer_url}/oauth/authorize",
            "token_endpoint": f"{issuer_url}/oauth/token",
            "userinfo_endpoint": f"{issuer_url}/userinfo",
            "jwks_uri": f"{issuer_url}/jwks.json",
            "scopes_supported": ["openid", "profile", "email", "roles"],
            "response_types_supported": ["code", "token", "id_token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "claims_supported": ["sub", "iss", "auth_time", "name", "email", "role", "department"]
        }

    def generate_id_token(self, user_id: str, email: str, role: str, department: str) -> Dict[str, Any]:
        """Compiles standard OpenID Connect ID token claims payload."""
        now = int(time.time())
        return {
            "iss": "http://localhost:8000",
            "sub": user_id,
            "aud": "LEAtTrace-frontend",
            "exp": now + 3600, # 1 Hour
            "iat": now,
            "auth_time": now,
            "nonce": str(uuid.uuid4()),
            "email": email,
            "role": role,
            "department": department
        }

oidc_provider = OIDCProvider()
