"""
Main entry point for the Trading Gateway.
"""

import asyncio
import sys
import os
import uvicorn
from trading_gateway.core.app import create_app

# Add shared module to path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shared"),
)

app = create_app()


async def startup():
    """Initialize services on startup."""
    print("🚀 Starting Trading Gateway services...")
    try:
        from management_server.tools.redis_streams_event_bus import (
            mcp_streams_event_bus,
        )
        from shared.config.redis_streams import redis_streams_config
        from trading_gateway.core.app import command_handler
        from trading_gateway.adapters.websocket_adapter import redis_event_listener

        print("🔌 Connecting to Redis...")
        await mcp_streams_event_bus.connect()
        print("✅ Redis connected")

        if mcp_streams_event_bus.redis:
            command_stream = redis_streams_config.MGMT_TRADING_COMMANDS
            consumer_group = redis_streams_config.TRADING_CONSUMERS

            print(f"📡 Subscribing to {command_stream} stream...")
            await mcp_streams_event_bus.subscribe(
                stream_name=command_stream,
                callback=command_handler,
                consumer_group=consumer_group,
            )
            print(f"✅ Subscribed to {command_stream} stream")

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
