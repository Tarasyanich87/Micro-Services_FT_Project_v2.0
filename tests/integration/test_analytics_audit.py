"""
Integration tests for Analytics and Audit APIs.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from management_server.core.app import create_application
from management_server.database import get_db
from management_server.models.base import Base


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_analytics.db"
engine = create_async_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio to use asyncio."""
    return "asyncio"


@pytest.fixture(scope="session")
async def setup_test_database():
    """Setup clean test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(setup_test_database):
    """Create test client."""
    app = create_application(session_factory=TestingSessionLocal)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
async def authenticated_client(client):
    """Create authenticated test client."""
    # Register test user
    register_data = {
        "username": "analytics_user",
        "email": "analytics@example.com",
        "password": "testpass123",
        "full_name": "Analytics Test User",
    }
    await client.post("/api/v1/auth/register", json=register_data)

    # Login
    login_data = {"username": "analytics_user", "password": "testpass123"}
    login_response = await client.post("/api/v1/auth/login/json", json=login_data)
    token = login_response.json()["access_token"]

    # Set authorization header
    client.headers["Authorization"] = f"Bearer {token}"
    return client


class TestAnalyticsAPI:
    """Integration tests for Analytics API endpoints."""

    @pytest.mark.asyncio
    async def test_get_performance_analytics_empty(self, authenticated_client):
        """Test performance analytics with no bot data."""
        client = authenticated_client

        response = await client.get("/api/v1/analytics/performance")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["total_trades"] == 0
        assert data["data"]["win_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_risk_analytics_empty(self, authenticated_client):
        """Test risk analytics with no bot data."""
        client = authenticated_client

        response = await client.get("/api/v1/analytics/risk")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["max_drawdown"] == 0.0

    @pytest.mark.asyncio
    async def test_get_portfolio_analytics_empty(self, authenticated_client):
        """Test portfolio analytics with no bot data."""
        client = authenticated_client

        response = await client.get("/api/v1/analytics/portfolio")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["portfolio_value"] == 0.0

    @pytest.mark.asyncio
    async def test_get_market_analytics_default(self, authenticated_client):
        """Test market analytics with default symbol."""
        client = authenticated_client

        response = await client.get("/api/v1/analytics/market")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        # Should either return data or error for CoinGecko API
        assert "data" in data

    @pytest.mark.asyncio
    async def test_get_market_analytics_custom_symbol(self, authenticated_client):
        """Test market analytics with custom symbol."""
        client = authenticated_client

        response = await client.get("/api/v1/analytics/market?symbol=ethereum")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_analytics_with_bot_data(self, authenticated_client):
        """Test analytics with actual bot data."""
        client = authenticated_client

        # Create a bot first
        bot_data = {
            "name": "AnalyticsTestBot",
            "description": "Bot for analytics testing",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 1000.0,
            "max_open_trades": 3,
            "config": {
                "trading_mode": "spot",
                "dry_run": True,
                "exchange": {"name": "binance"},
                "strategy": "TestStrategy",
            },
        }

        bot_response = await client.post("/api/v1/bots/", json=bot_data)
        assert bot_response.status_code == 201
        bot = bot_response.json()

        # Test portfolio analytics with bot data
        response = await client.get("/api/v1/analytics/portfolio")
        assert response.status_code == 200

        data = response.json()
        assert data["data"]["portfolio_value"] == 1000.0  # stake_amount

        # Clean up
        await client.delete(f"/api/v1/bots/{bot['id']}")


class TestAuditAPI:
    """Integration tests for Audit API endpoints."""

    @pytest.mark.asyncio
    async def test_get_audit_logs_empty(self, authenticated_client):
        """Test getting audit logs when none exist."""
        client = authenticated_client

        response = await client.get("/api/v1/audit/logs")
        assert response.status_code == 200

        logs = response.json()
        assert isinstance(logs, list)
        # Should contain logs from authentication and this request
        assert len(logs) >= 2  # login + this request

    @pytest.mark.asyncio
    async def test_get_audit_logs_pagination(self, authenticated_client):
        """Test audit logs pagination."""
        client = authenticated_client

        # Make several requests to generate audit logs
        for i in range(5):
            await client.get("/api/v1/bots/")

        # Test pagination
        response = await client.get("/api/v1/audit/logs?limit=3&skip=0")
        assert response.status_code == 200

        logs = response.json()
        assert len(logs) == 3

        # Test with offset
        response2 = await client.get("/api/v1/audit/logs?limit=2&skip=2")
        assert response2.status_code == 200

        logs2 = response2.json()
        assert len(logs2) == 2

    @pytest.mark.asyncio
    async def test_audit_log_structure(self, authenticated_client):
        """Test that audit logs have correct structure."""
        client = authenticated_client

        # Make a request
        await client.get("/api/v1/bots/")

        # Get audit logs
        response = await client.get("/api/v1/audit/logs?limit=1")
        logs = response.json()

        if logs:
            log_entry = logs[0]
            required_fields = [
                "id",
                "created_at",
                "username",
                "ip_address",
                "http_method",
                "path",
                "status_code",
            ]

            for field in required_fields:
                assert field in log_entry, f"Missing field: {field}"

            assert log_entry["http_method"] in ["GET", "POST", "PUT", "DELETE"]
            assert isinstance(log_entry["status_code"], int)

    @pytest.mark.asyncio
    async def test_audit_log_filtering(self, authenticated_client):
        """Test that audit logs are properly filtered by user."""
        client = authenticated_client

        # Make some requests
        await client.get("/api/v1/bots/")
        await client.get("/api/v1/strategies/")

        # Get logs
        response = await client.get("/api/v1/audit/logs")
        logs = response.json()

        # All logs should belong to the authenticated user
        for log in logs:
            if log["username"]:  # Some logs might not have username
                assert log["username"] == "analytics_user"


class TestAnalyticsAuditIntegration:
    """Integration tests combining analytics and audit functionality."""

    @pytest.mark.asyncio
    async def test_audit_logs_generated_for_analytics_requests(
        self, authenticated_client
    ):
        """Test that analytics requests generate audit logs."""
        client = authenticated_client

        # Get initial log count
        initial_response = await client.get("/api/v1/audit/logs")
        initial_logs = initial_response.json()

        # Make analytics requests
        await client.get("/api/v1/analytics/performance")
        await client.get("/api/v1/analytics/portfolio")
        await client.get("/api/v1/analytics/risk")

        # Check that new logs were created
        final_response = await client.get("/api/v1/audit/logs")
        final_logs = final_response.json()

        # Should have at least 3 more logs (plus the audit request itself)
        assert len(final_logs) >= len(initial_logs) + 3

        # Check that analytics endpoints are logged
        analytics_paths = [
            log["path"] for log in final_logs if "analytics" in log["path"]
        ]
        assert len(analytics_paths) >= 3

    @pytest.mark.asyncio
    async def test_analytics_with_bot_operations_audit(self, authenticated_client):
        """Test that bot operations generate proper audit logs and affect analytics."""
        client = authenticated_client

        # Create bot
        bot_data = {
            "name": "AuditAnalyticsBot",
            "description": "Bot for audit-analytics integration test",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 500.0,
            "max_open_trades": 2,
            "config": {
                "trading_mode": "spot",
                "dry_run": True,
                "exchange": {"name": "binance"},
                "strategy": "TestStrategy",
            },
        }

        bot_response = await client.post("/api/v1/bots/", json=bot_data)
        bot = bot_response.json()

        # Check analytics updated
        analytics_response = await client.get("/api/v1/analytics/portfolio")
        analytics_data = analytics_response.json()
        assert analytics_data["data"]["portfolio_value"] == 500.0

        # Check audit logs for bot creation
        audit_response = await client.get("/api/v1/audit/logs")
        audit_logs = audit_response.json()

        # Should have logs for bot creation
        bot_creation_logs = [
            log
            for log in audit_logs
            if "bots" in log["path"] and log["http_method"] == "POST"
        ]
        assert len(bot_creation_logs) >= 1

        # Clean up
        await client.delete(f"/api/v1/bots/{bot['id']}")

        # Verify analytics updated after deletion
        final_analytics = await client.get("/api/v1/analytics/portfolio")
        final_data = final_analytics.json()
        assert final_data["data"]["portfolio_value"] == 0.0
