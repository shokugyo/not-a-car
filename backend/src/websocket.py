from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections for realtime updates"""

    def __init__(self):
        # owner_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, owner_id: int):
        await websocket.accept()
        if owner_id not in self.active_connections:
            self.active_connections[owner_id] = set()
        self.active_connections[owner_id].add(websocket)

    def disconnect(self, websocket: WebSocket, owner_id: int):
        if owner_id in self.active_connections:
            self.active_connections[owner_id].discard(websocket)
            if not self.active_connections[owner_id]:
                del self.active_connections[owner_id]

    async def send_personal_message(self, message: dict, owner_id: int):
        if owner_id in self.active_connections:
            message_json = json.dumps(message)
            for connection in self.active_connections[owner_id]:
                try:
                    await connection.send_text(message_json)
                except Exception:
                    pass

    async def broadcast_to_owner(self, owner_id: int, event_type: str, data: dict):
        message = {
            "type": event_type,
            "data": data,
        }
        await self.send_personal_message(message, owner_id)


manager = ConnectionManager()


async def send_realtime_update(owner_id: int, update_type: str, data: dict):
    """
    Send realtime update to owner's connected clients.

    update_type can be:
    - "vehicle_status": Vehicle status changed
    - "earnings_update": New earnings recorded
    - "recommendation": New AI recommendation
    - "mode_change": Vehicle mode changed
    """
    await manager.broadcast_to_owner(owner_id, update_type, data)
