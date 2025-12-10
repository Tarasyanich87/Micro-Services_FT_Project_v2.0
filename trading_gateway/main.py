"""
Main entry point for the Trading Gateway.
"""

import asyncio
import uvicorn
from trading_gateway.core.app import create_app

app = create_app()


async def startup():
    """Initialize services on startup."""
    print("🚀 Starting Trading Gateway services...")
    try:
        from management_server.tools.redis_streams_event_bus import (
            mcp_streams_event_bus,
        )
        from trading_gateway.core.app import command_handler
        from trading_gateway.adapters.websocket_adapter import redis_event_listener

        print("🔌 Connecting to Redis...")
        await mcp_streams_event_bus.connect()
        print("✅ Redis connected")

        if mcp_streams_event_bus.redis:
            print("📡 Subscribing to bot_commands stream...")
            await mcp_streams_event_bus.subscribe(
                stream_name="bot_commands",
                callback=command_handler,
            )
            print("✅ Subscribed to bot_commands stream")

            print("📡 Starting WebSocket event listener...")
            asyncio.create_task(redis_event_listener())
            print("✅ WebSocket event listener started")
        else:
            print("❌ Could not connect to Redis")
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    # Initialize services
    asyncio.run(startup())

    # Note: reload=True is great for development but should be False in production.
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
