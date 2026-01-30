# ================================
# SensorPulse API - WebSocket Manager
# ================================

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocket
    user_id: Optional[str] = None
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    subscriptions: Set[str] = field(default_factory=set)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time sensor updates.
    
    Features:
    - Connection tracking
    - Broadcast to all clients
    - Topic-based subscriptions
    - Automatic cleanup on disconnect
    """
    
    def __init__(self):
        self._connections: Dict[str, ConnectionInfo] = {}
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
    ):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        async with self._lock:
            self._connections[client_id] = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
            )
        
        logger.info(f"WebSocket connected: {client_id}")
        
        # Send welcome message
        await self._send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if client_id in self._connections:
                del self._connections[client_id]
                logger.info(f"WebSocket disconnected: {client_id}")
    
    async def subscribe(self, client_id: str, topics: Set[str]):
        """Subscribe a client to specific device topics."""
        async with self._lock:
            if client_id in self._connections:
                self._connections[client_id].subscriptions.update(topics)
    
    async def unsubscribe(self, client_id: str, topics: Set[str]):
        """Unsubscribe a client from specific device topics."""
        async with self._lock:
            if client_id in self._connections:
                self._connections[client_id].subscriptions -= topics
    
    async def broadcast_reading(self, reading: Dict[str, Any]):
        """
        Broadcast a new sensor reading to all connected clients.
        
        Only sends to clients subscribed to the device's topic,
        or to all clients if they have no subscriptions (subscribe to all).
        """
        message = {
            "type": "reading",
            "data": reading,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        device_name = reading.get("device_name", "")
        topic = reading.get("topic", "")
        
        async with self._lock:
            disconnected = []
            
            for client_id, conn in self._connections.items():
                # Send if no subscriptions (all) or if subscribed to this device
                should_send = (
                    not conn.subscriptions or
                    device_name in conn.subscriptions or
                    topic in conn.subscriptions
                )
                
                if should_send:
                    try:
                        await conn.websocket.send_json(message)
                    except Exception as e:
                        logger.warning(f"Failed to send to {client_id}: {e}")
                        disconnected.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected:
                del self._connections[client_id]
    
    async def broadcast_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        async with self._lock:
            disconnected = []
            
            for client_id, conn in self._connections.items():
                try:
                    await conn.websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {e}")
                    disconnected.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected:
                del self._connections[client_id]
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send a message to a specific client."""
        async with self._lock:
            if client_id in self._connections:
                try:
                    await self._connections[client_id].websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {e}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)
    
    async def disconnect_all(self):
        """Disconnect all WebSocket connections (for shutdown)."""
        async with self._lock:
            for client_id, conn in list(self._connections.items()):
                try:
                    await conn.websocket.close(code=1001, reason="Server shutdown")
                except Exception as e:
                    logger.warning(f"Error closing connection {client_id}: {e}")
            self._connections.clear()
        logger.info("All WebSocket connections closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics."""
        return {
            "active_connections": len(self._connections),
            "clients": [
                {
                    "client_id": cid,
                    "user_id": conn.user_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "subscriptions": list(conn.subscriptions),
                }
                for cid, conn in self._connections.items()
            ],
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()
