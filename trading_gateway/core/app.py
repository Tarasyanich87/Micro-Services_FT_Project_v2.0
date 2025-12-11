"""
FastAPI application factory for the Trading Gateway.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
# from prometheus_fastapi_instrumentator import Instrumentator

from ..api.v1.router import api_router
from ..api.v1 import websocket
from ..adapters.websocket_adapter import redis_event_listener
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus
from shared.config.redis_streams import redis_streams_config
from ..services.bot_process_manager import BotProcessManager

logger = logging.getLogger(__name__)


# --- Global Instances ---
bot_process_manager = BotProcessManager(event_bus=mcp_streams_event_bus)


async def command_handler(event_message):
    """
    Asynchronously handles incoming commands from the Redis stream.
    """
    try:
        event_type = event_message.type
        event_data = event_message.data
        logger.info(
            f"Received command: Type={event_type}, Bot={event_data.get('bot_name', 'unknown')}"
        )

        if event_type == "START_BOT":
            await bot_process_manager.handle_start_bot_command(event_data)
            logger.info(
                f"✅ Processed START_BOT command for {event_data.get('bot_name')}"
            )
        elif event_type == "STOP_BOT":
            await bot_process_manager.handle_stop_bot_command(event_data)
            logger.info(
                f"✅ Processed STOP_BOT command for {event_data.get('bot_name')}"
            )
        elif event_type == "RESTART_BOT":
            await bot_process_manager.handle_restart_bot_command(event_data)
            logger.info(
                f"✅ Processed RESTART_BOT command for {event_data.get('bot_name')}"
            )
        elif event_type == "EMERGENCY_STOP_ALL":
            await bot_process_manager.handle_emergency_stop_all_command()
            logger.info("✅ Processed EMERGENCY_STOP_ALL command")
        else:
            logger.warning(f"Unknown command type received: {event_type}")

    except Exception as e:
        logger.error(f"❌ Error processing command {event_message.type}: {e}")
        logger.error(f"Command data: {event_message.data}")
        # Don't re-raise the exception to prevent the stream listener from crashing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle context manager to connect to Redis and start listeners.
    """
    print("🚀 Starting Trading Gateway lifespan")
    logger.info("🚀 Starting Trading Gateway")

    try:
        print("🔌 Connecting to Redis...")
        # Connect to Redis
        await mcp_streams_event_bus.connect()
        print("✅ Redis connected")

        # Subscribe to the command stream
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
            logger.info(f"✅ Successfully subscribed to {command_stream} stream")

            # Start WebSocket event listener
            print("📡 Starting WebSocket event listener...")
            asyncio.create_task(redis_event_listener())
            print("✅ WebSocket event listener started")
        else:
            print("❌ Could not subscribe to Redis streams: connection failed.")
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        import traceback

        print(traceback.format_exc())
        # Even if there's an error, we still yield to allow the app to start
    yield

    print("🛑 Shutting down Trading Gateway")
    try:
        await mcp_streams_event_bus.disconnect()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        print(f"❌ Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Creates and configures a FastAPI application."""
    app = FastAPI(
        title="Trading Gateway",
        description="A lightweight service for direct bot communication and command processing.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    # Add WebSocket routes
    websocket.add_websocket_routes(app)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics():
        """Prometheus metrics endpoint"""
        import time

        metrics_text = f"""# HELP trading_gateway_uptime_seconds Time since startup
# TYPE trading_gateway_uptime_seconds gauge
trading_gateway_uptime_seconds {time.time()}
# HELP trading_gateway_active_bots Number of active bots
# TYPE trading_gateway_active_bots gauge
trading_gateway_active_bots {len(bot_process_manager.running_bots)}
"""
        return Response(
            metrics_text, media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    return app
