# ================================
# SensorPulse API - WebSocket Routes
# ================================

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from websocket import ws_manager
from auth import decode_access_token

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/sensors")
async def websocket_sensors(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
):
    """
    WebSocket endpoint for real-time sensor updates.
    
    Connect to receive live sensor readings as they arrive.
    
    Query Parameters:
    - token: Optional JWT token for authentication
    
    Messages from server:
    - {"type": "connected", "client_id": "...", "timestamp": "..."}
    - {"type": "reading", "data": {...}, "timestamp": "..."}
    - {"type": "ping"}
    
    Messages to server:
    - {"type": "subscribe", "devices": ["device1", "device2"]}
    - {"type": "unsubscribe", "devices": ["device1"]}
    - {"type": "pong"}
    """
    # Generate unique client ID
    client_id = str(uuid.uuid4())
    
    # Validate token if provided
    user_id = None
    if token:
        token_data = decode_access_token(token)
        if token_data:
            user_id = token_data.user_id
    
    # Accept connection
    await ws_manager.connect(websocket, client_id, user_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            
            msg_type = data.get("type", "")
            
            if msg_type == "subscribe":
                devices = set(data.get("devices", []))
                await ws_manager.subscribe(client_id, devices)
                await websocket.send_json({
                    "type": "subscribed",
                    "devices": list(devices),
                })
            
            elif msg_type == "unsubscribe":
                devices = set(data.get("devices", []))
                await ws_manager.unsubscribe(client_id, devices)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "devices": list(devices),
                })
            
            elif msg_type == "pong":
                # Client responded to ping
                pass
            
            elif msg_type == "ping":
                # Client requesting ping
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except Exception as e:
        await ws_manager.disconnect(client_id)
        raise


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return ws_manager.get_stats()
