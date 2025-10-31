# websocket_manager.py
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.now(),
            "client_info": client_info or {}
        }
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json({
                **message,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        broadcast_message = {
            **message,
            "timestamp": datetime.now().isoformat(),
            "total_connections": len(self.active_connections)
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(broadcast_message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
        
        if disconnected:
            logger.info(f"Cleaned up {len(disconnected)} disconnected WebSocket connections")
    
    async def send_statistics_update(self, stats: Dict):
        """Send updated statistics to all connected clients"""
        await self.broadcast({
            "type": "statistics_update",
            "data": stats
        })
    
    async def send_new_prediction(self, prediction_data: Dict):
        """Send new prediction notification to all connected clients"""
        await self.broadcast({
            "type": "new_prediction",
            "data": prediction_data
        })
    
    async def send_system_message(self, message: str, level: str = "info"):
        """Send system message to all connected clients"""
        await self.broadcast({
            "type": "system_message",
            "message": message,
            "level": level
        })
    
    def get_connection_stats(self) -> Dict:
        """Get statistics about current connections"""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "connected_at": info["connected_at"].isoformat(),
                    "client_info": info["client_info"]
                }
                for info in self.connection_info.values()
            ]
        }