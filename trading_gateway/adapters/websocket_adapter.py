from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List, Optional
import logging
import json
import asyncio
from trading_gateway.services.ft_rest_client_service import ft_rest_client_service

# We need the event bus to listen to our own events
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus

logger = logging.getLogger(__name__)
router = APIRouter()

# ... (Protocol Models and Command Handlers are the same) ...


# --- Connection Management ---
class ClientConnection:
    def __init__(self, websocket: WebSocket, user_id: Optional[str] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.is_authenticated = False
        self.subscriptions: Set[str] = set()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, ClientConnection] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections[websocket] = ClientConnection(websocket, user_id)
        if user_id:
            self.active_connections[websocket].is_authenticated = True
        logger.info(f"New client connected: {websocket.client}, user_id: {user_id}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        logger.info(f"Client disconnected: {websocket.client}")

    async def broadcast_event(self, topic: str, event_name: str, data: dict):
        event_message = json.dumps(
            {
                "type": "EVENT",
                "payload": {
                    "topic": topic,
                    "event_name": event_name.upper(),
                    "data": data,
                },
            }
        )
        # Create a list of tasks to send the message to all subscribed clients
        tasks = []
        for client in self.active_connections.values():
            if client.is_authenticated and topic in client.subscriptions:
                tasks.append(client.websocket.send_text(event_message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(
                f"Broadcasted event '{event_name}' on topic '{topic}' to {len(tasks)} clients."
            )


manager = ConnectionManager()

# --- Redis Event Listener ---


async def handle_redis_event(event):
    """Handles events from Redis and broadcasts them to WebSocket clients."""
    event_name = None
    bot_name = None
    data = None

    try:
        # Handle both dict and EventMessage formats
        if hasattr(event, "data"):
            # EventMessage object
            event_data = event.data
            event_type = event.type
            source = event.source
        else:
            # Dict format
            event_data = event
            event_type = event.get("type", "unknown")
            source = event.get("source", "unknown")

        # Parse event_data if it's a string (JSON)
        if isinstance(event_data, str):
            event_data = json.loads(event_data)

        event_name = event_data.get("event_name", event_type)
        bot_name = event_data.get("bot_name")
        data = event_data

        if not event_name:
            logger.warning("Received Redis event without event_name")
            return

        # We assume all bot events belong to the 'bot_events' topic
        await manager.broadcast_event(
            "bot_events", event_name, {"bot_name": bot_name, "details": data}
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON event data: {e}")
    except Exception as e:
        logger.error(f"Error processing Redis event: {e}")


async def redis_event_listener():
    """Long-running task to listen for events on Redis and broadcast them."""
    logger.info("Starting Redis event listener for WebSocket broadcasting...")
    # We need to connect the bus first, which happens at app startup
    await mcp_streams_event_bus.subscribe("bot_events", handle_redis_event)


# ... (WebSocket Endpoint is the same, just need to add the listener to app startup) ...
