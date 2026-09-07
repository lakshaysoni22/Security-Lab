"""
LEAtTrace IAM — Security Headers Middleware.

Adds HSTS, CSP, CORS hardening, X-Frame-Options, and other security headers
to all HTTP responses. Integrates as FastAPI middleware.
"""

import time
import hashlib
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects enterprise security headers into all HTTP responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://127.0.0.1:* http://localhost:* ws://localhost:*; "
            "frame-ancestors 'none';"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(self), "
            "payment=(), usb=(), magnetometer=()"
        )

        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Request ID for tracing
        request_id = hashlib.sha256(f"{time.time()}{request.url.path}".encode()).hexdigest()[:16]
        response.headers["X-Request-ID"] = request_id

        # Server identification (obscured)
        response.headers["Server"] = "LEAtTrace-IAM/1.0"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter for API endpoints."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_counts = {}  # ip -> [(timestamp, count)]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        if client_ip in self._request_counts:
            self._request_counts[client_ip] = [
                (ts, c) for ts, c in self._request_counts[client_ip]
                if now - ts < self.window_seconds
            ]

        # Count requests
        entries = self._request_counts.get(client_ip, [])
        total = sum(c for _, c in entries)

        if total >= self.max_requests:
            return Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                headers={"Retry-After": str(self.window_seconds), "Content-Type": "application/json"},
            )

        entries.append((now, 1))
        self._request_counts[client_ip] = entries

        response = await call_next(request)

        # Add rate limit headers
        remaining = max(self.max_requests - total - 1, 0)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))

        return response
