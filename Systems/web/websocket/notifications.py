"""
WebSocket notifications handler.
"""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from Systems.core.events import event_bus
from Systems.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Store active connections
active_connections: dict[int, list[WebSocket]] = {}


class ConnectionManager:
    """Manager for WebSocket connections."""
    
    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: dict[int, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """Connect a WebSocket."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """Disconnect a WebSocket."""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            except ValueError:
                pass
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict[str, Any], user_id: int) -> None:
        """Send message to a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)


manager = ConnectionManager()


async def event_handler(event_name: str, data: Any) -> None:
    """
    Handle events from event bus.
    
    Args:
        event_name: Event name
        data: Event data
    """
    # Send notification to all users
    # In real implementation, filter by user permissions
    message = {
        "type": "notification",
        "event": event_name,
        "data": data,
    }
    
    for user_id in manager.active_connections:
        await manager.send_personal_message(message, user_id)


# Subscribe to event bus
# This should be done once on startup
async def subscribe_to_events() -> None:
    """Subscribe to event bus."""
    # Subscribe to common events
    await event_bus.subscribe("user.created", event_handler)
    await event_bus.subscribe("user.updated", event_handler)
    await event_bus.subscribe("module.enabled", event_handler)
    await event_bus.subscribe("module.disabled", event_handler)


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: int,
    # current_user: Any = Depends(get_current_user_ws),  # TODO: Implement WS auth
) -> None:
    """
    WebSocket endpoint for notifications.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID
        
    Example:
        ```python
        ws://localhost:8000/ws/notifications/123456
        ```
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to notification service",
            "user_id": user_id,
        })
        
        # Keep connection alive
        while True:
            # Wait for ping or disconnect
            try:
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    # Echo back (for testing)
                    await websocket.send_json({
                        "type": "echo",
                        "data": data,
                    })
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"Error in WebSocket connection for user {user_id}: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket, user_id)


