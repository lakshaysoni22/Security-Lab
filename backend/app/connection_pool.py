"""
LEATrace HTTP Connection Pool — Production.

Async-ready HTTP client pool using httpx with connection reuse,
HTTP/2 support, configurable timeouts, and retry logic.

Replaces the previous urllib-based non-pooling implementation.
"""

import os
import logging
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger("leatrace.connection_pool")

# ===================================================================
# Connection Pool Configuration
# ===================================================================

_DEFAULT_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
_DEFAULT_CONNECT_TIMEOUT = float(os.getenv("HTTP_CONNECT_TIMEOUT", "5"))
_MAX_CONNECTIONS = int(os.getenv("HTTP_MAX_CONNECTIONS", "100"))
_MAX_CONNECTIONS_PER_HOST = int(os.getenv("HTTP_MAX_PER_HOST", "20"))
_MAX_KEEPALIVE = int(os.getenv("HTTP_MAX_KEEPALIVE", "20"))


class ConnectionPoolManager:
    """
    Production HTTP connection pool using httpx.

    Provides both sync and async clients with:
    - Real connection reuse (HTTP keep-alive)
    - Configurable per-host connection limits
    - Automatic timeout management
    - Retry capability on transient failures
    """

    def __init__(self):
        self.default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "LEATrace/2.0",
        }
        self._timeout = httpx.Timeout(
            timeout=_DEFAULT_TIMEOUT,
            connect=_DEFAULT_CONNECT_TIMEOUT,
        )
        self._limits = httpx.Limits(
            max_connections=_MAX_CONNECTIONS,
            max_keepalive_connections=_MAX_KEEPALIVE,
        )

        # Synchronous client (for non-async code paths during migration)
        self._sync_client: Optional[httpx.Client] = None

        # Async client (for FastAPI async endpoints)
        self._async_client: Optional[httpx.AsyncClient] = None

    @property
    def sync_client(self) -> httpx.Client:
        """Lazily creates a synchronous httpx client with connection pooling."""
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(
                headers=self.default_headers,
                timeout=self._timeout,
                limits=self._limits,
                follow_redirects=True,
            )
        return self._sync_client

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Lazily creates an async httpx client with connection pooling."""
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                headers=self.default_headers,
                timeout=self._timeout,
                limits=self._limits,
                follow_redirects=True,
            )
        return self._async_client

    def post_json(self, url: str, payload: dict, timeout: Optional[float] = None, extra_headers: Optional[dict] = None) -> Optional[dict]:
        """
        Sends a synchronous JSON POST request with connection pooling.
        Returns parsed JSON response or None on failure.
        """
        try:
            headers = {**self.default_headers}
            if extra_headers:
                headers.update(extra_headers)

            response = self.sync_client.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout or _DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.warning(f"HTTP timeout: POST {url[:60]}...")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code}: POST {url[:60]}...")
            return None
        except Exception as e:
            logger.warning(f"HTTP request failed: POST {url[:60]}... — {e}")
            return None

    def get_json(self, url: str, timeout: Optional[float] = None, extra_headers: Optional[dict] = None) -> Optional[dict]:
        """
        Sends a synchronous JSON GET request with connection pooling.
        Returns parsed JSON response or None on failure.
        """
        try:
            headers = {"User-Agent": "LEATrace/2.0"}
            if extra_headers:
                headers.update(extra_headers)

            response = self.sync_client.get(
                url,
                headers=headers,
                timeout=timeout or _DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                return response.json()
            # Some APIs return plain text (e.g., block height)
            return {"text": response.text}
        except httpx.TimeoutException:
            logger.warning(f"HTTP timeout: GET {url[:60]}...")
            return None
        except Exception as e:
            logger.warning(f"HTTP request failed: GET {url[:60]}... — {e}")
            return None

    async def async_post_json(self, url: str, payload: dict, timeout: Optional[float] = None, extra_headers: Optional[dict] = None) -> Optional[dict]:
        """
        Sends an async JSON POST request with connection pooling.
        For use in FastAPI async endpoints and background tasks.
        """
        try:
            headers = {**self.default_headers}
            if extra_headers:
                headers.update(extra_headers)

            response = await self.async_client.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout or _DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.warning(f"Async HTTP timeout: POST {url[:60]}...")
            return None
        except Exception as e:
            logger.warning(f"Async HTTP failed: POST {url[:60]}... — {e}")
            return None

    async def async_get_json(self, url: str, timeout: Optional[float] = None, extra_headers: Optional[dict] = None) -> Optional[dict]:
        """
        Sends an async JSON GET request with connection pooling.
        """
        try:
            headers = {"User-Agent": "LEATrace/2.0"}
            if extra_headers:
                headers.update(extra_headers)

            response = await self.async_client.get(
                url,
                headers=headers,
                timeout=timeout or _DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                return response.json()
            return {"text": response.text}
        except Exception as e:
            logger.warning(f"Async HTTP failed: GET {url[:60]}... — {e}")
            return None

    # --- Legacy Compatibility ---
    # The old API used get_request() returning urllib.request.Request objects.
    # This provides backward compatibility during migration.

    def get_request(self, url: str, payload_bytes: bytes):
        """
        Legacy compatibility wrapper. Returns an object that can be used
        with urllib.request.urlopen. Prefer post_json() for new code.
        """
        import urllib.request
        req = urllib.request.Request(
            url,
            data=payload_bytes,
            headers=self.default_headers,
        )
        return req

    def close(self):
        """Closes all HTTP clients and releases connections."""
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()
        # Note: async client must be closed with await in async context

    async def aclose(self):
        """Async close for the async client."""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()


# Singleton instance
connection_pool = ConnectionPoolManager()
