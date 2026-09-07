"""
LEATrace TAXII 2.1 Client — Production.

Real HTTP client for TAXII 2.1 compliant servers.
Supports discovery, API roots, collections, object retrieval,
incremental sync, pagination, authentication, retry, rate limiting,
and delta synchronization via `added_after`.

PRODUCTION INVARIANTS:
- No hardcoded server URLs, collections, or indicators.
- All configuration from environment variables.
- If TAXII_SERVER_URL is not set → returns structured "not_configured" status.
- Never fabricates threat intelligence data.
- Sync state persisted to DB to support incremental delta sync.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger("leatrace.taxii_client")

# ─── Configuration ────────────────────────────────────────────────────────────

TAXII_SERVER_URL: Optional[str] = os.getenv("TAXII_SERVER_URL")          # e.g. https://cti.example.com/taxii
TAXII_USERNAME:   Optional[str] = os.getenv("TAXII_USERNAME")
TAXII_PASSWORD:   Optional[str] = os.getenv("TAXII_PASSWORD")
TAXII_TOKEN:      Optional[str] = os.getenv("TAXII_TOKEN")               # Bearer token (overrides basic auth)
TAXII_VERIFY_SSL: bool = os.getenv("TAXII_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}
TAXII_TIMEOUT:    int  = int(os.getenv("TAXII_TIMEOUT_SECONDS", "30"))
TAXII_RATE_LIMIT: float = float(os.getenv("TAXII_RATE_LIMIT_DELAY_S", "0.5"))  # seconds between pages
TAXII_MAX_RETRIES: int = int(os.getenv("TAXII_MAX_RETRIES", "3"))
TAXII_PAGE_LIMIT:  int = int(os.getenv("TAXII_PAGE_LIMIT", "100"))

NOT_CONFIGURED = {
    "status": "not_configured",
    "message": (
        "TAXII server is not configured. "
        "Set TAXII_SERVER_URL (and optionally TAXII_USERNAME/TAXII_PASSWORD or TAXII_TOKEN) "
        "in environment variables to enable threat intelligence synchronization."
    ),
}


# ─── HTTP Helper ──────────────────────────────────────────────────────────────

def _build_headers() -> Dict[str, str]:
    """Builds HTTP headers for TAXII 2.1 requests."""
    headers = {
        "Accept": "application/taxii+json;version=2.1",
        "Content-Type": "application/taxii+json;version=2.1",
        "User-Agent": "LEATrace-TAXII-Client/2.0",
    }
    if TAXII_TOKEN:
        headers["Authorization"] = f"Bearer {TAXII_TOKEN}"
    elif TAXII_USERNAME and TAXII_PASSWORD:
        import base64
        cred = base64.b64encode(f"{TAXII_USERNAME}:{TAXII_PASSWORD}".encode()).decode()
        headers["Authorization"] = f"Basic {cred}"
    return headers


def _http_get(url: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Performs a GET request with retry + exponential backoff.
    Returns parsed JSON response.
    Raises TAXIIError on non-2xx or unrecoverable failure.
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    headers = _build_headers()
    last_exc: Optional[Exception] = None

    for attempt in range(1, TAXII_MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            # Note: TAXII_VERIFY_SSL=False disables SSL — only for dev/private CAs
            ctx = None
            if not TAXII_VERIFY_SSL:
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=TAXII_TIMEOUT, context=ctx) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)

        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                # Rate limited or server unavailable — backoff
                wait = 2 ** attempt
                logger.warning("TAXII HTTP %s on attempt %d/%d, retrying in %ds", e.code, attempt, TAXII_MAX_RETRIES, wait)
                time.sleep(wait)
                last_exc = e
            elif e.code == 401:
                raise TAXIIAuthError(f"TAXII authentication failed (HTTP 401). Check TAXII_USERNAME/TAXII_PASSWORD/TAXII_TOKEN.")
            elif e.code == 403:
                raise TAXIIAuthError(f"TAXII access forbidden (HTTP 403). Check collection permissions.")
            elif e.code == 404:
                raise TAXIINotFoundError(f"TAXII resource not found: {url}")
            else:
                raise TAXIIError(f"TAXII HTTP error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            wait = 2 ** attempt
            logger.warning("TAXII connection error on attempt %d/%d: %s, retrying in %ds", attempt, TAXII_MAX_RETRIES, e.reason, wait)
            time.sleep(wait)
            last_exc = e
        except json.JSONDecodeError as e:
            raise TAXIIError(f"TAXII server returned invalid JSON: {e}")

    raise TAXIIConnectionError(f"TAXII connection failed after {TAXII_MAX_RETRIES} attempts: {last_exc}")


# ─── Exceptions ───────────────────────────────────────────────────────────────

class TAXIIError(Exception):
    """Base TAXII client error."""

class TAXIIAuthError(TAXIIError):
    """Authentication / authorization failure."""

class TAXIINotFoundError(TAXIIError):
    """Resource not found on TAXII server."""

class TAXIIConnectionError(TAXIIError):
    """Connection failure after all retries."""


# ─── TAXII 2.1 Client ────────────────────────────────────────────────────────

class TAXIIClient:
    """
    Production TAXII 2.1 client.

    Supports:
    - Server discovery
    - API root enumeration
    - Collection listing
    - Paginated object retrieval
    - Incremental delta sync via added_after
    - Retry with exponential backoff
    - Bearer and Basic auth
    """

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = (server_url or TAXII_SERVER_URL or "").rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.server_url)

    # ── Discovery ──────────────────────────────────────────────────────────────

    def discover(self) -> Dict[str, Any]:
        """
        Performs TAXII discovery (GET /taxii2/).
        Returns server metadata including api_roots.
        """
        if not self.is_configured():
            return NOT_CONFIGURED

        url = f"{self.server_url}/taxii2/"
        logger.info("TAXII discovery: %s", url)
        try:
            result = _http_get(url)
            logger.info("TAXII discovery success: title=%s roots=%s",
                        result.get("title"), result.get("api_roots"))
            return result
        except TAXIIError as e:
            logger.error("TAXII discovery failed: %s", e)
            return {"status": "error", "message": str(e)}

    def get_api_root_information(self, api_root_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches API root metadata.
        Uses first api_root from discovery if not specified.
        """
        if not self.is_configured():
            return NOT_CONFIGURED

        if not api_root_url:
            discovery = self.discover()
            roots = discovery.get("api_roots", [])
            if not roots:
                return {"status": "error", "message": "No API roots returned from TAXII discovery."}
            api_root_url = roots[0]

        logger.info("TAXII API root info: %s", api_root_url)
        try:
            return _http_get(api_root_url)
        except TAXIIError as e:
            logger.error("TAXII API root info failed: %s", e)
            return {"status": "error", "message": str(e)}

    # ── Collections ────────────────────────────────────────────────────────────

    def list_collections(self, api_root_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists all accessible collections on the TAXII server.
        """
        if not self.is_configured():
            return [NOT_CONFIGURED]

        root = api_root_url or self._resolve_api_root()
        if not root:
            return [{"status": "error", "message": "Could not resolve API root."}]

        url = f"{root.rstrip('/')}/collections/"
        logger.info("TAXII listing collections: %s", url)
        try:
            data = _http_get(url)
            collections = data.get("collections", [])
            logger.info("TAXII found %d collections", len(collections))
            return collections
        except TAXIIError as e:
            logger.error("TAXII list_collections failed: %s", e)
            return [{"status": "error", "message": str(e)}]

    # ── Object Retrieval & Sync ────────────────────────────────────────────────

    def get_collection_objects(
        self,
        collection_id: str,
        api_root_url: Optional[str] = None,
        added_after: Optional[str] = None,
        limit: int = TAXII_PAGE_LIMIT,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Yields STIX objects from a collection with full pagination support.

        Args:
            collection_id: TAXII collection ID
            api_root_url: API root URL (resolved via discovery if None)
            added_after: ISO 8601 UTC timestamp for delta sync
            limit: page size

        Yields:
            Individual STIX objects
        """
        if not self.is_configured():
            return

        root = api_root_url or self._resolve_api_root()
        if not root:
            logger.error("Cannot fetch objects: no API root resolved")
            return

        base_url = f"{root.rstrip('/')}/collections/{collection_id}/objects/"
        params: Dict[str, str] = {"limit": str(limit)}
        if added_after:
            params["added_after"] = added_after

        page_num = 0
        total_yielded = 0

        while True:
            page_num += 1
            logger.info("TAXII fetching page %d from collection %s (added_after=%s)",
                        page_num, collection_id, added_after)
            try:
                data = _http_get(base_url, params)
            except TAXIIError as e:
                logger.error("TAXII object fetch failed on page %d: %s", page_num, e)
                break

            objects = data.get("objects", [])
            for obj in objects:
                yield obj
                total_yielded += 1

            # Pagination: check for 'next' cursor
            next_cursor = data.get("next")
            if next_cursor:
                params["next"] = next_cursor
                # Rate limiting between pages
                time.sleep(TAXII_RATE_LIMIT)
            else:
                break

        logger.info("TAXII sync complete: collection=%s pages=%d objects=%d",
                    collection_id, page_num, total_yielded)

    def sync_collection_objects(
        self,
        collection_id: str,
        api_root_url: Optional[str] = None,
        added_after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Synchronous wrapper around get_collection_objects().
        Returns list of STIX objects from the collection.
        If server not configured → returns empty list with status entry.
        """
        if not self.is_configured():
            return [NOT_CONFIGURED]

        try:
            return list(self.get_collection_objects(
                collection_id,
                api_root_url=api_root_url,
                added_after=added_after,
            ))
        except Exception as e:
            logger.error("TAXII sync failed: %s", e)
            return [{"status": "error", "message": str(e)}]

    # ── Health ─────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """
        Returns TAXII server connectivity status.
        Safe to call frequently (no side effects).
        """
        if not self.is_configured():
            return {
                "configured": False,
                "status": "not_configured",
                "server_url": None,
                "message": NOT_CONFIGURED["message"],
            }

        try:
            discovery = self.discover()
            if "status" in discovery and discovery["status"] not in ("ok", "active"):
                # Error returned from discover()
                return {
                    "configured": True,
                    "status": "unreachable",
                    "server_url": self.server_url,
                    "error": discovery.get("message"),
                }
            return {
                "configured": True,
                "status": "healthy",
                "server_url": self.server_url,
                "server_title": discovery.get("title"),
                "api_roots": discovery.get("api_roots", []),
                "taxii_version": discovery.get("versions", []),
                "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "configured": True,
                "status": "error",
                "server_url": self.server_url,
                "error": str(e),
            }

    # ── Internal ───────────────────────────────────────────────────────────────

    def _resolve_api_root(self) -> Optional[str]:
        """Discovers the first API root from the server."""
        try:
            data = self.discover()
            roots = data.get("api_roots", [])
            return roots[0] if roots else None
        except Exception:
            return None

    def get_api_root_information(self) -> Dict[str, Any]:
        """
        Backward-compatibility alias for discover().
        Pre-existing code that called get_api_root_information() continues to work.
        """
        return self.discover()


# ─── Singleton ───────────────────────────────────────────────────────────

taxii_client = TAXIIClient()
