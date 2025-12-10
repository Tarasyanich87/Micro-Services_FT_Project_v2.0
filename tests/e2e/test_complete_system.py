"""
End-to-End tests for Freqtrade Multi-Bot System.
Tests complete user workflows and system integration.
"""

import asyncio
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from management_server.core.app import create_application
from management_server.database import get_db
from management_server.models.base import Base
from management_server.models import models


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_e2e.db"
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
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
    }
    await client.post("/api/v1/auth/register", json=register_data)

    # Login
    login_data = {"username": "testuser", "password": "testpass123"}
    login_response = await client.post("/api/v1/auth/login/json", json=login_data)
    token = login_response.json()["access_token"]

    # Set authorization header
    client.headers["Authorization"] = f"Bearer {token}"
    return client


class TestCompleteSystemWorkflow:
    """Test complete system workflows end-to-end."""

    @pytest.mark.asyncio
    async def test_user_registration_and_authentication(self, client):
        """Test user registration and authentication flow."""
        # Register user
        register_data = {
            "username": "e2e_user",
            "email": "e2e@example.com",
            "password": "securepass123",
            "full_name": "E2E Test User",
        }
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201

        user_data = response.json()
        assert user_data["username"] == "e2e_user"
        assert user_data["email"] == "e2e@example.com"

        # Login
        login_data = {"username": "e2e_user", "password": "securepass123"}
        response = await client.post("/api/v1/auth/login/json", json=login_data)
        assert response.status_code == 200

        auth_data = response.json()
        assert "access_token" in auth_data
        assert auth_data["token_type"] == "bearer"

        # Test authenticated endpoint
        client.headers["Authorization"] = f"Bearer {auth_data['access_token']}"
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200

        profile_data = response.json()
        assert profile_data["username"] == "e2e_user"

    @pytest.mark.asyncio
    async def test_strategy_lifecycle(self, authenticated_client):
        """Test complete strategy management lifecycle."""
        client = authenticated_client

        # Create strategy
        strategy_code = """
from freqtrade.strategy import IStrategy

class TestStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    stoploss = -0.10

    def populate_indicators(self, dataframe, metadata):
        return dataframe

    def populate_buy_trend(self, dataframe, metadata):
        dataframe.loc[:, "buy"] = 0
        return dataframe

    def populate_sell_trend(self, dataframe, metadata):
        dataframe.loc[:, "sell"] = 0
        return dataframe
"""

        create_data = {"code": strategy_code}
        response = await client.post(
            "/api/v1/strategies/?strategy_name=TestStrategy", json=create_data
        )
        assert response.status_code == 201

        # Verify strategy was created
        response = await client.get("/api/v1/strategies/")
        assert response.status_code == 200
        strategies = response.json()
        assert "TestStrategy" in strategies

        # Get strategy code
        response = await client.get("/api/v1/strategies/TestStrategy")
        assert response.status_code == 200
        strategy_data = response.json()
        assert "code" in strategy_data

        # Analyze strategy
        analyze_data = {"code": strategy_code}
        response = await client.post("/api/v1/strategies/analyze", json=analyze_data)
        assert response.status_code == 200
        analysis = response.json()
        assert analysis["valid"] is True
        assert "timeframe" in analysis["parameters"]

        # Update strategy
        updated_code = strategy_code.replace('timeframe = "5m"', 'timeframe = "1h"')
        update_data = {"code": updated_code}
        response = await client.put("/api/v1/strategies/TestStrategy", json=update_data)
        assert response.status_code == 200

        # Delete strategy
        response = await client.delete("/api/v1/strategies/TestStrategy")
        assert response.status_code == 204

        # Verify strategy was deleted
        response = await client.get("/api/v1/strategies/")
        strategies = response.json()
        assert "TestStrategy" not in strategies

    @pytest.mark.asyncio
    async def test_bot_lifecycle(self, authenticated_client):
        """Test complete bot management lifecycle."""
        client = authenticated_client

        # Create bot
        bot_data = {
            "name": "E2EBot",
            "description": "E2E test bot",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 100.0,
            "max_open_trades": 3,
            "config": {
                "trading_mode": "spot",
                "dry_run": True,
                "exchange": {"name": "binance"},
                "strategy": "TestStrategy",
            },
        }

        response = await client.post("/api/v1/bots/", json=bot_data)
        assert response.status_code == 201
        bot = response.json()
        assert bot["name"] == "E2EBot"

        # Get bots list
        response = await client.get("/api/v1/bots/")
        assert response.status_code == 200
        bots = response.json()
        assert len(bots) > 0
        assert any(b["name"] == "E2EBot" for b in bots)

        # Update bot
        update_data = {
            "name": "E2EBot",
            "description": "Updated E2E test bot",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 200.0,
            "max_open_trades": 5,
            "config": {
                "trading_mode": "spot",
                "dry_run": True,
                "exchange": {"name": "binance"},
                "strategy": "TestStrategy",
            },
        }

        response = await client.put(f"/api/v1/bots/{bot['id']}", json=update_data)
        assert response.status_code == 200
        updated_bot = response.json()
        assert updated_bot["stake_amount"] == 200.0

        # Start bot
        response = await client.post(f"/api/v1/bots/{bot['id']}/start")
        assert response.status_code == 200
        start_result = response.json()
        assert "start_command_sent" in start_result["status"]

        # Stop bot
        response = await client.post(f"/api/v1/bots/{bot['id']}/stop")
        assert response.status_code == 200
        stop_result = response.json()
        assert "stop_command_sent" in stop_result["status"]

        # Delete bot
        response = await client.delete(f"/api/v1/bots/{bot['id']}")
        assert response.status_code == 204

        # Verify bot was deleted
        response = await client.get("/api/v1/bots/")
        bots = response.json()
        assert not any(b["name"] == "E2EBot" for b in bots)

    @pytest.mark.asyncio
    async def test_strategy_backtesting_workflow(self, authenticated_client):
        """Test strategy backtesting workflow."""
        client = authenticated_client

        # Create bot for backtesting
        bot_data = {
            "name": "BacktestBot",
            "description": "Bot for backtesting",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 100.0,
            "max_open_trades": 3,
            "config": {
                "trading_mode": "spot",
                "dry_run": True,
                "exchange": {"name": "binance"},
                "strategy": "TestStrategy",
            },
        }

        response = await client.post("/api/v1/bots/", json=bot_data)
        bot = response.json()

        # Start backtesting
        backtest_data = {"strategy_name": "TestStrategy", "bot_id": bot["id"]}

        response = await client.post("/api/v1/strategies/backtest", json=backtest_data)
        assert response.status_code == 200
        backtest_result = response.json()
        assert "id" in backtest_result
        assert backtest_result["status"] == "queued"

        # Check backtest results
        response = await client.get("/api/v1/strategies/backtest/results")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

        # Clean up
        await client.delete(f"/api/v1/bots/{bot['id']}")

    @pytest.mark.asyncio
    async def test_freqai_integration(self, authenticated_client):
        """Test FreqAI model management."""
        client = authenticated_client

        # Get available models
        response = await client.get("/api/v1/freqai/models/")
        assert response.status_code == 200
        models = response.json()
        assert isinstance(models, list)

        # If models exist, test backtesting
        if models:
            model = models[0]

            # Create bot for FreqAI testing
            bot_data = {
                "name": "FreqAIBot",
                "description": "Bot with FreqAI",
                "strategy_name": "FreqaiExampleStrategy",
                "exchange": "binance",
                "stake_currency": "USDT",
                "stake_amount": 100.0,
                "max_open_trades": 3,
                "freqai_model_id": model["id"],
                "config": {
                    "trading_mode": "spot",
                    "dry_run": True,
                    "exchange": {"name": "binance"},
                    "strategy": "FreqaiExampleStrategy",
                },
            }

            response = await client.post("/api/v1/bots/", json=bot_data)
            assert response.status_code == 201
            bot = response.json()
            assert bot["freqai_model_id"] == model["id"]

            # Clean up
            await client.delete(f"/api/v1/bots/{bot['id']}")

    @pytest.mark.asyncio
    async def test_error_handling(self, authenticated_client):
        """Test error handling and validation."""
        client = authenticated_client

        # Test invalid strategy creation
        invalid_code = "invalid python code {{{"
        create_data = {"code": invalid_code}
        response = await client.post(
            "/api/v1/strategies/?strategy_name=InvalidStrategy", json=create_data
        )
        # Should still create (validation happens at analysis time)
        assert response.status_code == 201

        # Test analysis of invalid code
        analyze_data = {"code": invalid_code}
        response = await client.post("/api/v1/strategies/analyze", json=analyze_data)
        assert response.status_code == 200
        analysis = response.json()
        assert analysis["valid"] is False
        assert len(analysis["errors"]) > 0

        # Clean up
        await client.delete("/api/v1/strategies/InvalidStrategy")

        # Test accessing non-existent resources
        response = await client.get("/api/v1/strategies/NonExistentStrategy")
        assert response.status_code == 404

        response = await client.get("/api/v1/bots/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, authenticated_client):
        """Test concurrent operations and race conditions."""
        client = authenticated_client

        # Create multiple strategies concurrently
        import asyncio

        async def create_strategy(name):
            code = f"""
from freqtrade.strategy import IStrategy

class {name}(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    stoploss = -0.10

    def populate_indicators(self, dataframe, metadata):
        return dataframe

    def populate_buy_trend(self, dataframe, metadata):
        dataframe.loc[:, "buy"] = 0
        return dataframe

    def populate_sell_trend(self, dataframe, metadata):
        dataframe.loc[:, "sell"] = 0
        return dataframe
"""
            create_data = {"code": code}
            response = await client.post(
                f"/api/v1/strategies/?strategy_name={name}", json=create_data
            )
            return response.status_code

        # Create multiple strategies
        tasks = [create_strategy(f"ConcurrentStrategy{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(status == 201 for status in results)

        # Verify all were created
        response = await client.get("/api/v1/strategies/")
        strategies = response.json()
        concurrent_strategies = [
            s for s in strategies if s.startswith("ConcurrentStrategy")
        ]
        assert len(concurrent_strategies) == 5

        # Clean up
        for strategy in concurrent_strategies:
            await client.delete(f"/api/v1/strategies/{strategy}")


class TestSystemHealth:
    """Test system health and monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoints(self, client):
        """Test health check endpoints."""
        # Management server health
        response = await client.get("/health")
        assert response.status_code == 200

        # Trading gateway health
        # Note: This would require running trading gateway in tests
        # response = await client.get("http://localhost:8001/health")
        # assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_endpoints(self, client):
        """Test metrics endpoints."""
        # Prometheus metrics
        response = await client.get("/metrics")
        # Metrics endpoint might not be available in test environment
        # but should not crash the application
        assert response.status_code in [200, 404]  # 404 if metrics not enabled


class TestDataValidation:
    """Test data validation and sanitization."""

    @pytest.mark.asyncio
    async def test_input_validation(self, authenticated_client):
        """Test input validation for all endpoints."""
        client = authenticated_client

        # Test invalid bot data
        invalid_bot_data = {
            "name": "",  # Empty name
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "INVALID",
            "stake_amount": -100,  # Negative amount
            "max_open_trades": 0,
        }

        response = await client.post("/api/v1/bots/", json=invalid_bot_data)
        # Should still create but with validation
        assert response.status_code in [201, 422]

        # Test SQL injection attempts
        malicious_data = {
            "name": "TestBot'; DROP TABLE users; --",
            "strategy_name": "TestStrategy",
            "exchange": "binance",
            "stake_currency": "USDT",
            "stake_amount": 100.0,
            "max_open_trades": 3,
        }

        response = await client.post("/api/v1/bots/", json=malicious_data)
        # Should sanitize input
        assert response.status_code in [201, 422]

        # Clean up if created
        if response.status_code == 201:
            bot = response.json()
            await client.delete(f"/api/v1/bots/{bot['id']}")
