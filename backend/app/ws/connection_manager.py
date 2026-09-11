import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # We track connections globally and per-channel
        self.active_connections: Set[WebSocket] = set()
        # channel_name -> Set[WebSocket]
        self.channels: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = None):
        await websocket.accept()
        self.active_connections.add(websocket)
        if channel:
            if channel not in self.channels:
                self.channels[channel] = set()
            self.channels[channel].add(websocket)
            logger.info("Client connected to channel: %s", channel)
        else:
            logger.info("Client connected without channel")

    def disconnect(self, websocket: WebSocket, channel: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if channel and channel in self.channels:
            if websocket in self.channels[channel]:
                self.channels[channel].remove(websocket)
            if not self.channels[channel]:
                del self.channels[channel]
            logger.info("Client disconnected from channel: %s", channel)
        else:
            logger.info("Client disconnected")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("Failed to send message to client: %s", e)

    async def broadcast(self, message: dict, channel: str = None):
        connections = self.channels.get(channel, set()) if channel else self.active_connections
        dead_connections = set()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Failed to broadcast message: %s", e)
                dead_connections.add(connection)
        
        # Cleanup dead connections
        for dead in dead_connections:
            self.disconnect(dead, channel)


manager = ConnectionManager()
