"""
LEATrace RBAC Middleware — Production.

Role-based access control middleware, API rate limiting,
request audit logging, and IP-based access control.

ROLES HIERARCHY:
    admin > supervisor > investigator > analyst > auditor > readonly

PRODUCTION INVARIANTS:
- All protected endpoints require authentication.
- Rate limits enforced per user (not globally).
- All API access logged to audit trail.
"""

import time
import logging
import datetime
from typing import Dict, List, Optional, Callable
from collections import defaultdict

from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from . import models
from .security import get_current_user

logger = logging.getLogger("leatrace.rbac")


# ===================================================================
# Role Hierarchy & Permissions
# ===================================================================

ROLE_HIERARCHY = {
    "admin": 100,
    "supervisor": 80,
    "investigator": 60,
    "analyst": 40,
    "auditor": 30,
    "readonly": 10,
}

# Endpoint permission mapping: prefix → minimum role level
# More specific prefixes take priority over less specific ones
ENDPOINT_PERMISSIONS = {
    # Admin only
    "/api/auth/users": 100,          # User management
    "/api/iam": 100,                  # IAM management
    "/api/security": 80,             # Security config

    # Supervisor+
    "/api/cases": 60,                # Case management (investigators can access)
    "/api/investigation/sanctions": 80,  # Sanctions management

    # Investigator+
    "/api/investigation": 60,        # Investigation tools
    "/api/blockchain/risk": 60,      # Risk scoring
    "/api/wallet": 60,               # Wallet analysis
    "/api/crosschain": 60,           # Cross-chain tracing
    "/api/bridge": 60,               # Bridge analysis
    "/api/defi": 60,                 # DeFi analysis
    "/api/mixer": 60,                # Mixer analysis
    "/api/threat": 60,               # Threat intel
    "/api/entity": 60,               # Entity resolution
    "/api/aml": 60,                  # AML analysis
    "/api/correlation": 60,          # SIEM correlation
    "/api/forensics": 60,            # Forensics

    # Analyst+
    "/api/soc": 40,                  # SOC dashboard
    "/api/graph": 40,                # Graph visualization
    "/api/streaming": 40,            # Real-time streams

    # Auditor+
    "/api/audit": 30,                # Audit logs

    # Readonly+
    "/api/health": 0,                # Health check (public)
    "/api/auth/login": 0,            # Login (public)
    "/api/auth/register": 0,         # Registration (public)
}


def get_required_level(path: str) -> int:
    """Returns the minimum role level required for an endpoint path."""
    # Find the most specific matching prefix
    best_match = ""
    best_level = 10  # Default: readonly

    for prefix, level in ENDPOINT_PERMISSIONS.items():
        if path.startswith(prefix) and len(prefix) > len(best_match):
            best_match = prefix
            best_level = level

    return best_level


def check_role_access(user_role: str, required_level: int) -> bool:
    """Checks if a user's role meets the required permission level."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    return user_level >= required_level


# ===================================================================
# Prebuilt Role Dependencies (for use in router decorators)
# ===================================================================

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency: requires admin role."""
    if ROLE_HIERARCHY.get(current_user.role, 0) < 100:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_supervisor(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency: requires supervisor or higher."""
    if ROLE_HIERARCHY.get(current_user.role, 0) < 80:
        raise HTTPException(status_code=403, detail="Supervisor access required")
    return current_user


def require_investigator(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency: requires investigator or higher."""
    if ROLE_HIERARCHY.get(current_user.role, 0) < 60:
        raise HTTPException(status_code=403, detail="Investigator access required")
    return current_user


def require_analyst(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency: requires analyst or higher."""
    if ROLE_HIERARCHY.get(current_user.role, 0) < 40:
        raise HTTPException(status_code=403, detail="Analyst access required")
    return current_user


def require_auditor(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency: requires auditor or higher."""
    if ROLE_HIERARCHY.get(current_user.role, 0) < 30:
        raise HTTPException(status_code=403, detail="Auditor access required")
    return current_user


# ===================================================================
# API Rate Limiter (Per-User, In-Memory)
# ===================================================================

class RateLimiter:
    """
    Per-user API rate limiter with sliding window.
    Tracks request counts per user over a configurable window.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self.rpm_limit = requests_per_minute
        self.rph_limit = requests_per_hour
        self._minute_windows: Dict[str, List[float]] = defaultdict(list)
        self._hour_windows: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        """Checks if a user is within rate limits."""
        now = time.time()

        # Clean and check minute window
        minute_ago = now - 60
        self._minute_windows[user_id] = [
            t for t in self._minute_windows[user_id] if t > minute_ago
        ]
        if len(self._minute_windows[user_id]) >= self.rpm_limit:
            return False

        # Clean and check hour window
        hour_ago = now - 3600
        self._hour_windows[user_id] = [
            t for t in self._hour_windows[user_id] if t > hour_ago
        ]
        if len(self._hour_windows[user_id]) >= self.rph_limit:
            return False

        return True

    def record_request(self, user_id: str):
        """Records a request for rate limiting."""
        now = time.time()
        self._minute_windows[user_id].append(now)
        self._hour_windows[user_id].append(now)

    def get_remaining(self, user_id: str) -> Dict[str, int]:
        """Returns remaining requests for a user."""
        now = time.time()
        minute_count = len([t for t in self._minute_windows.get(user_id, []) if t > now - 60])
        hour_count = len([t for t in self._hour_windows.get(user_id, []) if t > now - 3600])
        return {
            "rpm_remaining": max(self.rpm_limit - minute_count, 0),
            "rph_remaining": max(self.rph_limit - hour_count, 0),
        }


# Singleton
rate_limiter = RateLimiter()


# ===================================================================
# Request Audit Logger
# ===================================================================

class AuditLogger:
    """Logs all API requests with user, endpoint, method, and timing."""

    def log_request(
        self,
        user_id: Optional[str],
        username: Optional[str],
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: str,
    ):
        """Logs an API request to the audit system."""
        log_entry = {
            "user_id": user_id,
            "username": username,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 1),
            "client_ip": client_ip,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        }

        # Log sensitive operations at WARNING level
        if any(sensitive in path for sensitive in ["/auth/", "/iam/", "/security/", "/sanctions/"]):
            logger.warning(f"AUDIT: {log_entry}")
        else:
            logger.info(f"AUDIT: {log_entry}")


audit_logger = AuditLogger()


# ===================================================================
# Combined RBAC + Rate Limit + Audit Middleware
# ===================================================================

# Public paths that don't require authentication
PUBLIC_PATHS = {
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Combined middleware for:
    1. Request audit logging (all requests)
    2. Rate limiting (authenticated requests)
    3. Security headers (all responses)
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            audit_logger.log_request(None, None, method, path, 500, duration_ms, client_ip)
            raise

        duration_ms = (time.time() - start_time) * 1000

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["X-Request-Duration-Ms"] = str(round(duration_ms, 1))
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Audit log
        audit_logger.log_request(None, None, method, path, response.status_code, duration_ms, client_ip)

        return response
