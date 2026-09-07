import json
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from ..event_broker import broker
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/api/streaming", tags=["Real-Time Event Streaming System"])

async def verify_websocket_token(token: str) -> Optional[models.User]:
    """Verifies JWT token passed over WebSocket query parameters."""
    if not token:
        return None
    try:
        db = SessionLocal()
        from jose import jwt
        from ..security import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            db.close()
            return None
        user = db.query(models.User).filter(models.User.id == user_id).first()
        db.close()
        return user
    except Exception:
        return None

@router.websocket("/alerts")
async def stream_security_alerts(websocket: WebSocket, token: str = Query(None)):
    """WebSocket stream dispatching real-time fraud alerts to client dashboard."""
    user = await verify_websocket_token(token)
    if not user:
        await websocket.accept()
        await websocket.close(code=4003) # Unauthorized
        return

    await websocket.accept()
    
    try:
        # Subscribe to alert_stream channel
        async for alert_msg in broker.subscribe("alert_stream"):
            await websocket.send_text(alert_msg)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass

@router.websocket("/wallet/{address}")
async def stream_wallet_monitoring(websocket: WebSocket, address: str, token: str = Query(None)):
    """WebSocket stream dispatching real-time transactions matching monitored address."""
    user = await verify_websocket_token(token)
    if not user:
        await websocket.accept()
        await websocket.close(code=4003) # Unauthorized
        return

    await websocket.accept()
    address_lower = address.lower().strip()
    
    try:
        # Subscribe to transaction_stream channel
        async for tx_msg in broker.subscribe("transaction_stream"):
            tx_data = json.loads(tx_msg)
            tx_from = tx_data.get("from", "").lower()
            tx_to = tx_data.get("to", "").lower()
            
            # Send message if matches monitored address
            if tx_from == address_lower or tx_to == address_lower:
                await websocket.send_text(tx_msg)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass
