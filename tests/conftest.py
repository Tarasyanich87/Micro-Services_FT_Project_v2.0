"""
Pytest configuration and shared fixtures for multi-service testing.
Supports all 4 microservices: Management Server, Trading Gateway, Backtesting Server, FreqAI Server.
"""

import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Dict, Any, Tuple
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Management Server imports
from management_server.core.app import create_application
from management_server.database import get_db
from management_server.models.base import Base
from management_server.models import models

# Trading Gateway imports
from trading_gateway.core.app import create_app as create_trading_gateway_app

# Shared test database for management server
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override database dependency for tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio to use asyncio."""
    return "asyncio"


@pytest.fixture(scope="function")
async def setup_test_database():
    """
    Ensures a clean database for every single test.
    1. Deletes old DB file if it exists.
    2. Creates all tables.
    3. Yields to let the test run.
    4. Drops all tables.
    """
    if os.path.exists("./test.db"):
        os.remove("./test.db")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ===== MANAGEMENT SERVER FIXTURES =====


@pytest.fixture(scope="function")
async def management_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the Management Server (Port 8002).
    This client will have a fresh, clean database for every test function.
    """
    application = create_application(
        "full_featured", session_factory=TestingSessionLocal
    )
    application.dependency_overrides[get_db] = override_get_db

    async with application.router.lifespan_context(application):
        async with AsyncClient(
            transport=ASGITransport(app=application), base_url="http://test"
        ) as client:
            yield client


@pytest.fixture(scope="function")
async def management_auth_headers(management_client: AsyncClient) -> Dict[str, str]:
    """Fixture to create a user and return auth headers for Management Server tests."""
    task = asyncio.current_task()
    task_name = task.get_name() if task else "default"
    username = f"testuser_{task_name}"
    password = "password"

    await management_client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
        },
    )
    response = await management_client.post(
        "/api/v1/auth/login/json",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===== TRADING GATEWAY FIXTURES =====


@pytest.fixture(scope="function")
async def trading_gateway_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the Trading Gateway (Port 8001).
    Mocks Redis connections for isolated testing.
    """
    # Mock Redis connections to avoid external dependencies
    with patch(
        "management_server.tools.redis_streams_event_bus.mcp_streams_event_bus"
    ) as mock_bus:
        mock_bus.connect = AsyncMock()
        mock_bus.subscribe = AsyncMock()
        mock_bus.publish = AsyncMock()
        mock_bus.redis = AsyncMock()

        application = create_trading_gateway_app()

        async with application.router.lifespan_context(application):
            async with AsyncClient(
                transport=ASGITransport(app=application), base_url="http://test"
            ) as client:
                yield client


# ===== BACKTESTING SERVER FIXTURES =====


@pytest.fixture(scope="function")
async def backtesting_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the Backtesting Server (Port 8003).
    """
    # Import here to avoid issues during test collection
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    # Mock imports that might fail
    try:
        from backtesting_server.main import app as backtesting_app

        # Mock Redis client to avoid external dependencies
        with patch("shared.redis_client.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.set = AsyncMock()
            mock_redis.delete = AsyncMock()

            async with AsyncClient(
                transport=ASGITransport(app=backtesting_app), base_url="http://test"
            ) as client:
                yield client
    except ImportError:
        # If import fails, skip this fixture
        pytest.skip("Backtesting server not available for testing")


# ===== FREQAI SERVER FIXTURES =====


@pytest.fixture(scope="function")
async def freqai_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the FreqAI Server (Port 8004).
    """
    # Import here to avoid issues during test collection
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    try:
        from freqai_server.main import app as freqai_app

        # Mock Redis client to avoid external dependencies
        with patch("shared.redis_client.redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.set = AsyncMock()
            mock_redis.delete = AsyncMock()

            async with AsyncClient(
                transport=ASGITransport(app=freqai_app), base_url="http://test"
            ) as client:
                yield client
    except ImportError:
        # If import fails, skip this fixture
        pytest.skip("FreqAI server not available for testing")


# ===== LEGACY ALIASES FOR BACKWARD COMPATIBILITY =====


@pytest.fixture(scope="function")
async def app_client(management_client: AsyncClient) -> AsyncClient:
    """Legacy alias for management_client."""
    return management_client


@pytest.fixture(scope="function")
async def auth_headers(management_auth_headers: Dict[str, str]) -> Dict[str, str]:
    """Legacy alias for management_auth_headers."""
    return management_auth_headers


# ===== SHARED TEST UTILITIES =====


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Shared test configuration."""
    return {
        "management_server_url": "http://localhost:8002",
        "trading_gateway_url": "http://localhost:8001",
        "backtesting_server_url": "http://localhost:8003",
        "freqai_server_url": "http://localhost:8004",
        "test_user": {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        },
    }


@pytest.fixture(scope="function")
async def authenticated_clients(
    test_config: Dict[str, Any],
    management_client: AsyncClient,
    trading_gateway_client: AsyncClient,
) -> Dict[str, Tuple[AsyncClient | None, Dict[str, str] | None]]:
    """Fixture providing authenticated clients for all services."""
    # Authenticate with management server
    await management_client.post(
        "/api/v1/auth/register",
        json=test_config["test_user"],
    )
    login_response = await management_client.post(
        "/api/v1/auth/login/json",
        json={
            "username": test_config["test_user"]["username"],
            "password": test_config["test_user"]["password"],
        },
    )
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    return {
        "management": (management_client, auth_headers),
        "trading_gateway": (
            trading_gateway_client,
            None,
        ),  # Trading gateway doesn't require auth
        "backtesting": (
            None,
            None,
        ),  # Will be added when backtesting_client is available
        "freqai": (None, None),  # Will be added when freqai_client is available
    }
