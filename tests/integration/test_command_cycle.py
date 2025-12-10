import asyncio
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from management_server.models.models import User, Bot, BotCreate
from management_server.tools.redis_streams_event_bus import EventMessage

# Mark all tests in this file as async and ensure a clean database
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("setup_test_database")]


@pytest.fixture
async def test_user(app_client: AsyncClient) -> User:
    """Fixture to create a test user and return the User object."""
    # This assumes your test setup for app_client can handle DB operations.
    # In a real app, you might create the user directly in the DB.
    response = await app_client.post(
        "/api/v1/auth/register",
        json={
            "username": "cycleuser",
            "email": "cycle@test.com",
            "password": "password",
        },
    )
    assert response.status_code == 200
    user_data = response.json()
    # This is a simplified way; a better fixture would return the ORM object.
    return User(**user_data, id=user_data["id"])


@pytest.fixture
async def test_bot(app_client: AsyncClient, auth_headers: dict) -> Bot:
    """Fixture to create a test bot and return the ORM object."""
    bot_data = {
        "name": "test_cycle_bot",
        "strategy_name": "test_strategy",
        "exchange": "binance",
        "stake_currency": "USDT",
        "stake_amount": 100.0,
    }
    create_response = await app_client.post(
        "/api/v1/bots/", json=bot_data, headers=auth_headers
    )
    assert create_response.status_code == 201
    bot_id = create_response.json()["id"]

    # Fetch the bot properly to get a session-attached ORM instance
    get_response = await app_client.get(f"/api/v1/bots/{bot_id}", headers=auth_headers)
    assert get_response.status_code == 200

    # This is still not a real ORM object, but it's the full data.
    # The error is likely elsewhere, but this is a good practice.
    # Let's return the ID which is all we really need.
    bot_json = get_response.json()
    return Bot(**bot_json)


async def test_start_bot_command_cycle(
    app_client: AsyncClient, auth_headers: dict, test_bot: Bot
):
    """
    Tests the full command cycle:
    1. API call to start a bot.
    2. Verify command is published to Redis.
    3. Simulate gateway response event.
    4. Verify bot status is updated in the database.
    """
    # Patch the 'publish' method of the event bus
    with patch(
        "management_server.tools.redis_streams_event_bus.RedisStreamsEventBus.publish",
        new_callable=AsyncMock,
    ) as mock_publish:
        # 1. API call to start a bot
        response = await app_client.post(
            f"/api/v1/bots/{test_bot.id}/start", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "start_command_sent"

        # 2. Verify command is published to Redis
        await asyncio.sleep(0.1)  # allow time for the async call
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args[1]
        assert call_args["stream_name"] == "mcp_commands"
        assert call_args["event_type"] == "START_BOT"
        assert call_args["event_data"]["bot_name"] == test_bot.name

        # Check bot status is 'starting'
        bot_status_resp = await app_client.get(
            f"/api/v1/bots/{test_bot.id}", headers=auth_headers
        )
        assert bot_status_resp.json()["status"] == "starting"

    # 3. Simulate gateway response event by directly calling the handler
    from management_server.services.bot_event_handler import BotEventHandler
    from ..conftest import TestingSessionLocal

    # Create a fresh session from the testing factory
    async with TestingSessionLocal() as session:
        # The handler needs a factory, so we wrap the session in a lambda
        bot_event_handler = BotEventHandler(lambda: session)

        # Craft a realistic event message
        # The handler expects the raw message from redis, not a Pydantic model
        response_event = {
            "type": "BOT_STARTED",
            "data": {
                "bot_name": test_bot.name,
                "details": {"status": "running", "pid": 1234, "port": 8081},
            },
            "source": "trading_gateway",
        }

        # We need to wrap it in a mock object that has the fields the handler expects
        class MockEventMessage:
            def __init__(self, event_type, event_data):
                self.type = event_type
                self.data = event_data

        await bot_event_handler.handle_event(
            MockEventMessage(
                event_type="BOT_STARTED",
                event_data={"bot_name": test_bot.name, "pid": 1234, "port": 8081},
            )
        )

    # 4. Verify bot status is updated in the database
    # No need to sleep, the call was synchronous
    final_bot_resp = await app_client.get(
        f"/api/v1/bots/{test_bot.id}", headers=auth_headers
    )
    assert final_bot_resp.status_code == 200
    final_bot_data = final_bot_resp.json()
    assert final_bot_data["status"] == "running"
