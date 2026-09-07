"""
LEATrace RPC Response Cache — Production.

Caches JSON-RPC responses in Redis with configurable TTLs.
Falls back gracefully to no caching if Redis is unavailable.
"""

import json
import logging
from typing import Optional, Any

from .database import get_redis_client

logger = logging.getLogger("leatrace.rpc_cache")


class RPCCacheManager:
    """Caches RPC responses in Redis. No-op if Redis unavailable."""

    def __init__(self):
        self.enabled = True

    def get(self, key: str) -> Optional[Any]:
        """Gets cached JSON-RPC payload from Redis."""
        if not self.enabled:
            return None
        client = get_redis_client()
        if client is None:
            return None
        try:
            val = client.get(f"rpc_cache:{key}")
            if val:
                return json.loads(val) if isinstance(val, str) else json.loads(val.decode("utf-8"))
        except Exception as e:
            logger.debug(f"RPC cache get failed: {e}")
        return None

    def set(self, key: str, value: Any, expire_seconds: int = 60) -> None:
        """Caches JSON-RPC payload in Redis."""
        if not self.enabled:
            return
        client = get_redis_client()
        if client is None:
            return
        try:
            client.setex(f"rpc_cache:{key}", expire_seconds, json.dumps(value))
        except Exception as e:
            logger.debug(f"RPC cache set failed: {e}")

    def invalidate(self, key: str) -> None:
        """Removes a cached entry."""
        client = get_redis_client()
        if client is None:
            return
        try:
            client.delete(f"rpc_cache:{key}")
        except Exception:
            pass


rpc_cache = RPCCacheManager()
