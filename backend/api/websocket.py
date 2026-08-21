from fastapi import WebSocket
from models.schemas import WSMessage
import json
import logging
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

class WebSocketManager:
    def __init__(self):
        self._connections: list[WebSocket] = []
        self._logger = logging.getLogger('websocket')
    
    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
    
    async def broadcast(self, message: WSMessage) -> None:
        data = message.model_dump(mode='json')
        msg_str = json.dumps(data, default=json_serial)
        
        disconnected = []
        for connection in self._connections:
            try:
                await connection.send_text(msg_str)
            except Exception as e:
                self._logger.warning(f"Error sending message to client: {e}")
                disconnected.append(connection)
                
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_health(self, health_snapshot) -> None:
        msg = WSMessage(type="health_update", data=health_snapshot.model_dump(mode='json'))
        await self.broadcast(msg)
    
    async def broadcast_incident(self, incident) -> None:
        msg = WSMessage(type="new_incident", data=incident.model_dump(mode='json'))
        await self.broadcast(msg)
    
    @property
    def connection_count(self) -> int:
        return len(self._connections)
