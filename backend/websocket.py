"""WebSocket connection manager for streaming responses."""

import asyncio
import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time streaming."""

    def __init__(self):
        """Initialize the connection manager."""
        # Maps conversation_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, conversation_id: str):
        """
        Accept a new WebSocket connection and register it.

        Args:
            websocket: The WebSocket connection to register
            conversation_id: ID of the conversation this connection is for
        """
        await websocket.accept()

        async with self._lock:
            if conversation_id not in self.active_connections:
                self.active_connections[conversation_id] = []
            self.active_connections[conversation_id].append(websocket)

        logger.info(f"WebSocket connected for conversation {conversation_id}. "
                   f"Total connections: {len(self.active_connections[conversation_id])}")

    async def disconnect(self, websocket: WebSocket, conversation_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
            conversation_id: ID of the conversation
        """
        async with self._lock:
            if conversation_id in self.active_connections:
                if websocket in self.active_connections[conversation_id]:
                    self.active_connections[conversation_id].remove(websocket)

                # Clean up empty conversation lists
                if not self.active_connections[conversation_id]:
                    del self.active_connections[conversation_id]

        logger.info(f"WebSocket disconnected for conversation {conversation_id}")

    async def send_message(self, message: dict, conversation_id: str):
        """
        Send a message to all connections for a conversation.

        Args:
            message: Dictionary to send as JSON
            conversation_id: ID of the conversation
        """
        if conversation_id not in self.active_connections:
            return

        # Create a copy of the connection list to avoid modification during iteration
        connections = list(self.active_connections.get(conversation_id, []))

        # Track disconnected websockets
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected during send for {conversation_id}")
                disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if conversation_id in self.active_connections:
                        if ws in self.active_connections[conversation_id]:
                            self.active_connections[conversation_id].remove(ws)

    async def broadcast(self, message: dict, conversation_id: str):
        """
        Broadcast a message to all clients subscribed to a conversation.

        This is an alias for send_message for semantic clarity.

        Args:
            message: Dictionary to send as JSON
            conversation_id: ID of the conversation
        """
        await self.send_message(message, conversation_id)

    async def send_token(self, token: str, conversation_id: str, model: str = None, stage: str = None):
        """
        Send a single token to all connections.

        Args:
            token: The token string to send
            conversation_id: ID of the conversation
            model: Optional model identifier
            stage: Optional stage identifier (e.g., "stage1", "stage2")
        """
        message = {
            "type": "token",
            "token": token,
            "model": model,
            "stage": stage
        }
        await self.send_message(message, conversation_id)

    async def send_event(self, event_type: str, data: dict, conversation_id: str):
        """
        Send a structured event to all connections.

        Args:
            event_type: Type of event (e.g., "stage_start", "model_complete")
            data: Event data
            conversation_id: ID of the conversation
        """
        message = {
            "type": event_type,
            "data": data
        }
        await self.send_message(message, conversation_id)

    async def send_error(self, error: str, conversation_id: str):
        """
        Send an error message to all connections.

        Args:
            error: Error message
            conversation_id: ID of the conversation
        """
        message = {
            "type": "error",
            "error": error
        }
        await self.send_message(message, conversation_id)

    async def send_completion(self, conversation_id: str):
        """
        Send a completion signal to all connections.

        Args:
            conversation_id: ID of the conversation
        """
        message = {
            "type": "complete"
        }
        await self.send_message(message, conversation_id)

    def get_connection_count(self, conversation_id: str) -> int:
        """
        Get the number of active connections for a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(conversation_id, []))

    def get_total_connections(self) -> int:
        """
        Get the total number of active connections across all conversations.

        Returns:
            Total number of active connections
        """
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
connection_manager = ConnectionManager()
