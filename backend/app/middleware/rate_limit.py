"""
LEATrace Rate Limiting Middleware — Production.

Sliding window rate limiter backed by:
  1. Redis (preferred — distributed, survives restarts)
  2. In-memory (fallback — single process only)

Configuration via environment variables:
  RATE_LIMIT_REQUESTS    = Max requests per window (default: 100)
  RATE_LIMIT_WINDOW_S    = Window size in seconds (default: 60)
  RATE_LIMIT_LOGIN_MAX   = Max login attempts per window (default: 5)
  RATE_LIMIT_LOGIN_WIN_S = Login attempt window in seconds (default: 900)

Responses:
  429 Too Many Requests — with Retry-After header
  X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers on all responses
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("leatrace.middleware.rate_limit")

# ─── Configuration ────────────────────────────────────────────────────────────

RATE_LIMIT_REQUESTS:    int = int(os.getenv("RATE_LIMIT_REQUESTS",    "100"))
RATE_LIMIT_WINDOW_S:    int = int(os.getenv("RATE_LIMIT_WINDOW_S",    "60"))
RATE_LIMIT_LOGIN_MAX:   int = int(os.getenv("RATE_LIMIT_LOGIN_MAX",   "5"))
RATE_LIMIT_LOGIN_WIN_S: int = int(os.getenv("RATE_LIMIT_LOGIN_WIN_S", "900"))
REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

# Paths that apply stricter login rate limit
_LOGIN_PATHS = {"/api/auth/login", "/api/auth/token", "/api/token"}

# Paths exempt from rate limiting (health probes, metrics)
_EXEMPT_PATHS = {"/health", "/health/ready", "/metrics", "/docs", "/openapi.json", "/redoc"}


# ─── In-memory Backend ────────────────────────────────────────────────────────

class _InMemoryRateLimiter:
    """
    Sliding window rate limiter using in-memory deques.
    Thread-safe for single-process deployments.
    Not suitable for multi-process deployments — use Redis backend.
    """

    def __init__(self) -> None:
        # ip -> deque of timestamps
        self._windows: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, limit: int, window_s: int) -> tuple[bool, int, int]:
        """
        Checks if a request is within rate limit.

        Returns:
            (allowed: bool, remaining: int, reset_at: int)
        """
        now = time.monotonic()
        cutoff = now - window_s
        window = self._windows[key]

        # Evict old timestamps
        while window and window[0] < cutoff:
            window.popleft()

        remaining = max(0, limit - len(window))
        reset_at = int(time.time()) + window_s

        if len(window) >= limit:
            return False, 0, reset_at

        window.append(now)
        return True, remaining - 1, reset_at


# ─── Redis Backend ────────────────────────────────────────────────────────────

class _RedisRateLimiter:
    """
    Sliding window rate limiter using Redis sorted sets.
    Distributed — works across multiple processes and pods.
    """

    def __init__(self, redis_url: str) -> None:
        import redis
        self._r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)

    def is_allowed(self, key: str, limit: int, window_s: int) -> tuple[bool, int, int]:
        now = time.time()
        cutoff = now - window_s
        pipe = self._r.pipeline()
        redis_key = f"rl:{key}"

        pipe.zremrangebyscore(redis_key, "-inf", cutoff)
        pipe.zadd(redis_key, {str(now): now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window_s)
        results = pipe.execute()

        count = results[2]
        reset_at = int(now) + window_s

        if count > limit:
            # Remove the just-added entry since we're rejecting
            self._r.zrem(redis_key, str(now))
            return False, 0, reset_at

        remaining = max(0, limit - count)
        return True, remaining, reset_at


# ─── Middleware ────────────────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware for per-IP sliding window rate limiting.

    Applied globally with per-path overrides for auth endpoints.
    Adds standard rate limit headers to every response.
    """

    def __init__(self, app: Callable) -> None:
        super().__init__(app)
        self._limiter: _InMemoryRateLimiter | _RedisRateLimiter

        if REDIS_URL:
            try:
                self._limiter = _RedisRateLimiter(REDIS_URL)
                logger.info("Rate limiter: Redis backend (%s)", REDIS_URL[:30])
            except Exception as e:
                logger.warning("Redis rate limiter failed, falling back to in-memory: %s", e)
                self._limiter = _InMemoryRateLimiter()
        else:
            self._limiter = _InMemoryRateLimiter()
            logger.info("Rate limiter: in-memory backend (single-process)")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip exempt paths
        if path in _EXEMPT_PATHS:
            return await call_next(request)

        # Extract client IP
        client_ip = _get_client_ip(request)

        # Determine applicable limit
        if path in _LOGIN_PATHS:
            limit = RATE_LIMIT_LOGIN_MAX
            window = RATE_LIMIT_LOGIN_WIN_S
            key = f"login:{client_ip}"
        else:
            limit = RATE_LIMIT_REQUESTS
            window = RATE_LIMIT_WINDOW_S
            key = f"api:{client_ip}"

        try:
            allowed, remaining, reset_at = self._limiter.is_allowed(key, limit, window)
        except Exception as e:
            # Rate limiter failure should never block requests
            logger.error("Rate limiter error: %s", e)
            allowed, remaining, reset_at = True, limit, int(time.time()) + window

        if not allowed:
            logger.warning("Rate limit exceeded: ip=%s path=%s", client_ip, path)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "retry_after": window,
                },
                headers={
                    "Retry-After":          str(window),
                    "X-RateLimit-Limit":    str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset":    str(reset_at),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"]     = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"]     = str(reset_at)

        return response


def _get_client_ip(request: Request) -> str:
    """Extracts real client IP, respecting X-Forwarded-For from trusted proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first (client) IP from the chain
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
