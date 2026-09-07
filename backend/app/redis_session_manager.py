from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional


class RedisSessionStore:
    def __init__(self, use_redis: bool = True, redis_client: Optional[Any] = None, redis_url: Optional[str] = None):
        self.use_redis = use_redis
        self.redis_client = redis_client
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._connect()

    def _connect(self) -> None:
        if not self.use_redis or self.redis_client is not None:
            return
        try:
            import redis

            self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception:
            self.redis_client = None
            self.use_redis = False

    def _store_session(self, session_id: str, payload: Dict[str, Any]) -> None:
        if self.use_redis and self.redis_client is not None:
            self.redis_client.set(f"session:{session_id}", json.dumps(payload))
            return
        self._sessions[session_id] = payload

    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.use_redis and self.redis_client is not None:
            raw = self.redis_client.get(f"session:{session_id}")
            if raw is None:
                return None
            return json.loads(raw)
        return self._sessions.get(session_id)

    def create_session(self, user_id: str, device_id: str, refresh_token: str) -> str:
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        payload = {
            "user_id": user_id,
            "device_id": device_id,
            "refresh_token": refresh_token,
            "active": True,
        }
        self._store_session(session_id, payload)
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._load_session(session_id)

    def rotate_refresh_token(self, session_id: str, new_refresh_token: str) -> Optional[str]:
        session = self._load_session(session_id)
        if not session:
            return None
        session["refresh_token"] = new_refresh_token
        self._store_session(session_id, session)
        return new_refresh_token

    def revoke_session(self, session_id: str) -> bool:
        session = self._load_session(session_id)
        if not session:
            return False
        session["active"] = False
        self._store_session(session_id, session)
        return True
