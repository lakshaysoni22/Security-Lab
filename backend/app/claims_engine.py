"""
LEAtTrace IAM — Claims Engine.

Maps OpenID Connect scopes to user claims. Provides custom claims
for role, department, permissions, and security clearance.
"""

import time
from typing import Dict, Any, List, Optional


# Scope-to-claims mapping
SCOPE_CLAIMS_MAP = {
    "openid": ["sub", "iss", "aud", "exp", "iat", "auth_time"],
    "profile": ["name", "preferred_username", "updated_at"],
    "email": ["email", "email_verified"],
    "roles": ["role", "roles", "permissions"],
    "department": ["department", "organization", "designation"],
    "clearance": ["security_clearance", "clearance_level"],
    "investigation": ["active_cases", "case_assignments"],
}


class ClaimsEngine:
    """Generates and resolves OpenID Connect claims from scopes and user attributes."""

    def resolve_scopes(self, scopes: List[str]) -> List[str]:
        """Returns the list of claims associated with the requested scopes."""
        claims = set()
        for scope in scopes:
            scope_claims = SCOPE_CLAIMS_MAP.get(scope, [])
            claims.update(scope_claims)
        return sorted(claims)

    def generate_id_token_claims(
        self,
        user_id: str,
        email: str,
        username: str,
        role: str,
        department: str,
        issuer: str,
        audience: str,
        nonce: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        clearance_level: int = 1,
        permissions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generates complete ID token claims payload based on requested scopes."""
        now = int(time.time())
        requested_scopes = scopes or ["openid", "profile", "email", "roles"]

        claims = {
            "iss": issuer,
            "sub": user_id,
            "aud": audience,
            "exp": now + 3600,
            "iat": now,
            "auth_time": now,
        }

        if nonce:
            claims["nonce"] = nonce

        # Scope-based claim population
        if "profile" in requested_scopes:
            claims["name"] = username
            claims["preferred_username"] = username
            claims["updated_at"] = now

        if "email" in requested_scopes:
            claims["email"] = email
            claims["email_verified"] = True

        if "roles" in requested_scopes:
            claims["role"] = role
            claims["roles"] = [role]
            claims["permissions"] = permissions or []

        if "department" in requested_scopes:
            claims["department"] = department
            claims["organization"] = "LEAtTrace Cyber Investigation"
            claims["designation"] = role.replace("_", " ").title()

        if "clearance" in requested_scopes:
            claims["security_clearance"] = clearance_level
            claims["clearance_level"] = clearance_level

        return claims

    def generate_userinfo_response(
        self,
        user_id: str,
        email: str,
        username: str,
        role: str,
        department: str,
        clearance_level: int = 1,
        scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generates the /userinfo endpoint response."""
        requested_scopes = scopes or ["openid", "profile", "email", "roles"]
        response = {"sub": user_id}

        if "profile" in requested_scopes:
            response["name"] = username
            response["preferred_username"] = username
            response["updated_at"] = int(time.time())

        if "email" in requested_scopes:
            response["email"] = email
            response["email_verified"] = True

        if "roles" in requested_scopes:
            response["role"] = role
            response["roles"] = [role]

        if "department" in requested_scopes:
            response["department"] = department

        if "clearance" in requested_scopes:
            response["security_clearance"] = clearance_level

        return response


claims_engine = ClaimsEngine()
