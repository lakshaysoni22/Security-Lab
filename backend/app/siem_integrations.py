from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
from urllib import request, error


class SIEMIntegrationService:
    def __init__(self, endpoint: Optional[str] = None, auth_token: Optional[str] = None, timeout: int = 3) -> None:
        self.endpoint = endpoint or os.getenv("SIEM_ENDPOINT")
        self.auth_token = auth_token or os.getenv("SIEM_AUTH_TOKEN")
        self.timeout = timeout
        self.events: List[Dict[str, Any]] = []

    def send_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "status": "queued",
            "event": event,
            "timestamp": int(time.time()),
        }
        self.events.append(record)

        if self.endpoint:
            payload = json.dumps(record).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            try:
                req = request.Request(self.endpoint, data=payload, headers=headers, method="POST")
                with request.urlopen(req, timeout=self.timeout) as response:
                    response_body = response.read().decode("utf-8")
                return {"status": "sent", "event": event, "response": response_body}
            except (error.URLError, error.HTTPError, TimeoutError):
                return {"status": "queued", "event": event, "reason": "delivery_failed"}

        return record
