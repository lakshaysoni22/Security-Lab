import json
import asyncio
from typing import AsyncGenerator, Dict, List, Any
from .database import get_redis_client

class EventBroker:
    def __init__(self):
        self.redis = None
        self.local_listeners: Dict[str, List[asyncio.Queue]] = {}
        self.lock = asyncio.Lock()
        
        try:
            self.redis = get_redis_client()
            if self.redis and hasattr(self.redis, 'store'):
                self.redis = None
            elif self.redis:
                self.redis.ping()
        except Exception:
            self.redis = None

    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publishes an event message to the specified stream channel."""
        message_str = json.dumps(message)
        
        if self.redis:
            try:
                # Use Redis Pub/Sub stream integration
                self.redis.publish(channel, message_str)
                return
            except Exception:
                pass
                
        # In-memory Asyncio Queue fallback (Event-driven Broker Emulator)
        async with self.lock:
            if channel in self.local_listeners:
                for queue in self.local_listeners[channel]:
                    await queue.put(message_str)

    async def subscribe(self, channel: str) -> AsyncGenerator[str, None]:
        """Subscribes to a stream channel and yields real-time messages."""
        if self.redis:
            try:
                pubsub = self.redis.pubsub()
                pubsub.subscribe(channel)
                
                # Check for messages in background loop
                while True:
                    # Redis yields messages as dictionaries
                    msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if msg and msg['type'] == 'message':
                        yield msg['data'].decode('utf-8')
                    await asyncio.sleep(0.1)
            except Exception:
                pass

        # Fallback to local asyncio queue subscription
        queue = asyncio.Queue()
        async with self.lock:
            if channel not in self.local_listeners:
                self.local_listeners[channel] = []
            self.local_listeners[channel].append(queue)

        try:
            while True:
                msg = await queue.get()
                yield msg
        finally:
            async with self.lock:
                if channel in self.local_listeners:
                    self.local_listeners[channel].remove(queue)

# Global event broker instance
broker = EventBroker()
