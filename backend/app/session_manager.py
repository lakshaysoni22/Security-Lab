import time
from typing import Dict, List, Any

# Local session registry: session_id -> { user_id, device_name, last_active, ip_address }
SESSIONS = {} # type: Dict[str, Dict]

class SessionManager:
    def create_session(self, session_id: str, user_id: str, device_name: str, ip_address: str) -> Dict[str, Any]:
        """Creates a session registration and enforces max concurrent session limits."""
        # Enforce maximum of 3 concurrent sessions per user
        user_sessions = [sid for sid, sess in SESSIONS.items() if sess["user_id"] == user_id]
        if len(user_sessions) >= 3:
            # Terminate oldest session
            oldest_sid = sorted(user_sessions, key=lambda sid: SESSIONS[sid]["last_active"])[0]
            SESSIONS.pop(oldest_sid, None)
            
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "device_name": device_name,
            "ip_address": ip_address,
            "last_active": int(time.time())
        }
        SESSIONS[session_id] = session_data
        return session_data

    def terminate_session(self, session_id: str) -> bool:
        """Terminates an active session."""
        if session_id in SESSIONS:
            SESSIONS.pop(session_id)
            return True
        return False

    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Lists active sessions for a user."""
        return [sess for sess in SESSIONS.values() if sess["user_id"] == user_id]

session_manager = SessionManager()
