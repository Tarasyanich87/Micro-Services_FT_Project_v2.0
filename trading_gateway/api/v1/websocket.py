"""
WebSocket endpoints for real-time communication.
Provides authenticated WebSocket connections for real-time updates.
"""

import logging
from typing import Dict, Any
from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    Query,
    HTTPException,
)
import jwt
from datetime import datetime

from management_server.core.config import settings
from management_server.auth.jwt import ALGORITHM, SECRET_KEY
from trading_gateway.adapters.websocket_adapter import manager, ClientConnection

logger = logging.getLogger(__name__)


async def authenticate_websocket(websocket: WebSocket, token: str | None) -> str:
    """Authenticate WebSocket connection using JWT token."""
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        await websocket.close(code=4001, reason="Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")


async def handle_client_message(
    websocket: WebSocket, message: Dict[str, Any], user_id: str
):
    """Handle incoming messages from WebSocket clients."""
    message_type = message.get("type")

    if message_type == "SUBSCRIBE":
        # Handle topic subscriptions
        topics = message.get("topics", [])
        connection = manager.active_connections.get(websocket)
        if connection:
            connection.subscriptions.update(topics)
            logger.info(f"User {user_id} subscribed to topics: {topics}")

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "SUBSCRIBED",
                    "topics": list(connection.subscriptions),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    elif message_type == "UNSUBSCRIBE":
        # Handle topic unsubscriptions
        topics = message.get("topics", [])
        connection = manager.active_connections.get(websocket)
        if connection:
            connection.subscriptions.difference_update(topics)
            logger.info(f"User {user_id} unsubscribed from topics: {topics}")

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "UNSUBSCRIBED",
                    "topics": list(connection.subscriptions),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    elif message_type == "PING":
        # Handle ping/pong for connection health
        await websocket.send_json(
            {"type": "PONG", "timestamp": datetime.utcnow().isoformat()}
        )

    else:
        logger.warning(f"Unknown message type from user {user_id}: {message_type}")


def add_websocket_routes(app):
    """Add WebSocket routes to the FastAPI app."""

    @app.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        token: str | None = Query(None, description="JWT authentication token"),
    ):
        """
        Main WebSocket endpoint for real-time communication.

        Provides authenticated WebSocket connections for:
        - Real-time bot status updates
        - System health notifications
        - Live trading events

        Authentication: JWT token required via query parameter
        Protocol: JSON messages with type/payload structure
        """
        user_id = await authenticate_websocket(websocket, token)

        # Connect to WebSocket manager
        await manager.connect(websocket, user_id)

        logger.info(f"WebSocket connection established for user {user_id}")

        try:
            # Send welcome message
            await websocket.send_json(
                {
                    "type": "WELCOME",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Connected to Freqtrade Multi-Bot System",
                }
            )

            # Main message handling loop
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_json()
                    await handle_client_message(websocket, data, user_id)

                except ValueError:
                    # Invalid JSON
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "error": "Invalid JSON format",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
            manager.disconnect(websocket)

        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            try:
                await websocket.send_json(
                    {
                        "type": "ERROR",
                        "error": "Internal server error",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            except:
                pass  # Connection might be closed
            manager.disconnect(websocket)

    @app.websocket("/ws/mcp")
    async def mcp_websocket_endpoint(websocket: WebSocket):
        """
        WebSocket endpoint for MCP (Model Context Protocol) agents.

        Specialized endpoint for AI agents and external integrations
        using the MCP protocol for enhanced communication.
        """
        # MCP handshake
        await websocket.accept()

        await websocket.send_json(
            {
                "type": "HANDSHAKE",
                "protocol": "mcp",
                "version": "1.0",
                "capabilities": [
                    "real_time_events",
                    "command_execution",
                    "data_streaming",
                ],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        logger.info("MCP WebSocket connection established")

        try:
            while True:
                data = await websocket.receive_json()

                # Handle MCP protocol messages
                if data.get("type") == "SUBSCRIBE":
                    # MCP subscription handling
                    await websocket.send_json(
                        {
                            "type": "SUBSCRIBED",
                            "topics": data.get("topics", []),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                elif data.get("type") == "COMMAND":
                    # MCP command execution
                    command = data.get("command")
                    # Process MCP command
                    result = {"status": "executed", "command": command}
                    await websocket.send_json(
                        {
                            "type": "COMMAND_RESULT",
                            "result": result,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                else:
                    await websocket.send_json(
                        {
                            "type": "ERROR",
                            "error": f"Unknown MCP message type: {data.get('type')}",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

        except WebSocketDisconnect:
            logger.info("MCP WebSocket disconnected")
        except Exception as e:
            logger.error(f"MCP WebSocket error: {e}")
            try:
                await websocket.send_json(
                    {
                        "type": "ERROR",
                        "error": "MCP protocol error",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            except:
                pass
