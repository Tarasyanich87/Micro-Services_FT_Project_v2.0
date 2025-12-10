"""
FastAPI application factory with profile-based configuration.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator

from management_server.api.v1.router import api_router
from management_server.core.config import settings
from management_server.core.logging import setup_logging, get_logger
from management_server.database import close_database, init_database, SessionLocal
from management_server.middleware.audit_middleware import AuditMiddleware
from management_server.middleware.error_handling import APIError, api_error_handler
from management_server.middleware.logging import RequestLoggingMiddleware
from management_server.middleware.rate_limiting import create_limiter
from management_server.services.trading_gateway_client import (
    close_trading_gateway_client,
)
from management_server.services.freqai_server_client import (
    close_freqai_server_client,
)
from management_server.tools.redis_streams_event_bus import (
    RedisStreamsEventBus,
    mcp_streams_event_bus,
    core_streams_event_bus,
)

# Import Prometheus after other imports to avoid conflicts
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Instrumentator = None

logger = logging.getLogger(__name__)


def lifespan_factory(session_factory):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Application lifecycle context manager.
        """
        profile = app.state.profile
        logger.info(f"🚀 Starting Management Server (profile: {profile})")
        await init_database()
        logger.info("✅ Database initialized")

        # Connect to both event buses
        await core_streams_event_bus.connect()
        await mcp_streams_event_bus.connect()
        logger.info("✅ Redis Streams connected")

        # Subscribe to the events stream from the trading gateway
        if mcp_streams_event_bus.redis:
            from management_server.services.bot_event_handler import BotEventHandler

            bot_event_handler = BotEventHandler(session_factory)
            await mcp_streams_event_bus.subscribe(
                stream_name="mcp_events", callback=bot_event_handler.handle_event
            )
        else:
            logger.error("Could not subscribe to mcp_events: Redis connection failed.")

        yield

        logger.info("🛑 Shutting down Management Server")
        await close_database()
        logger.info("✅ Database connections closed")
        await core_streams_event_bus.disconnect()
        await mcp_streams_event_bus.disconnect()
        logger.info("✅ Redis Streams disconnected")
        await close_trading_gateway_client()
        logger.info("✅ Trading Gateway client shut down")
        await close_freqai_server_client()
        logger.info("✅ FreqAI Server client shut down")

    return lifespan


def create_application(
    profile: str = "full_featured", session_factory=SessionLocal
) -> FastAPI:
    """
    Create FastAPI application with profile-based configuration.

    Args:
        profile: Application profile ("trading_only", "trading_audit", "full_featured")

    Returns:
        Configured FastAPI application
    """
    valid_profiles = ["trading_only", "trading_audit", "full_featured"]
    if profile not in valid_profiles:
        raise ValueError(f"Invalid profile: {profile}. Must be one of {valid_profiles}")

    # Setup centralized logging
    setup_logging(
        log_level=settings.LOG_LEVEL, json_format=settings.ENVIRONMENT == "production"
    )

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        openapi_url="/api/v1/openapi.json" if profile != "trading_only" else None,
        docs_url="/docs" if profile != "trading_only" else None,
        redoc_url="/redoc" if profile != "trading_only" else None,
        lifespan=lifespan_factory(session_factory),
    )

    app.state.profile = profile

    # Middleware setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.ENVIRONMENT == "production":
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # Rate limiting
    limiter = create_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Custom middleware
    app.add_middleware(AuditMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_exception_handler(APIError, api_error_handler)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": str(request.url),
            },
        )

    # Routers
    app.include_router(api_router, prefix="/api/v1")
    _add_profile_specific_routes(app, profile)

    # Test endpoint
    @app.get("/api/v1/test", tags=["Test"])
    async def test_endpoint():
        return {"message": "Test endpoint works", "status": "ok"}

    # Prometheus metrics
    if PROMETHEUS_AVAILABLE:
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=[
                "/metrics",
                "/health",
                "/docs",
                "/redoc",
                "/openapi.json",
            ],
            env_var_name="ENABLE_METRICS",
            inprogress_name="inprogress",
            inprogress_labels=True,
        )
        instrumentator.instrument(app).expose(
            app, endpoint="/metrics", include_in_schema=False
        )
        logger.info("✅ Prometheus metrics enabled at /metrics")
    else:
        logger.warning("⚠️ Prometheus not available, metrics disabled")

    return app


def _get_profile_features(profile: str) -> list[str]:
    """Get features available for the given profile."""
    features: Dict[str, list[str]] = {
        "trading_only": ["bot_management", "basic_monitoring"],
        "trading_audit": [
            "bot_management",
            "monitoring",
            "analytics",
            "audit_logs",
        ],
        "full_featured": [
            "bot_management",
            "monitoring",
            "analytics",
            "audit_logs",
            "admin_panel",
            "advanced_features",
            "ai_integration",
        ],
    }
    return features.get(profile, [])


def _add_profile_specific_routes(app: FastAPI, profile: str):
    """Add profile-specific routes."""

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "management_server",
            "profile": profile,
            "version": settings.PROJECT_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/api/v1/info", tags=["Info"])
    async def get_system_info():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.PROJECT_VERSION,
            "profile": profile,
            "features": _get_profile_features(profile),
        }

    if profile in ["trading_audit", "full_featured"]:
        # Add audit routes here if they exist
        pass

    if profile == "full_featured":
        # Add admin routes here if they exist
        pass
