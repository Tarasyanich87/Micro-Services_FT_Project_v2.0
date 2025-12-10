import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

# Mark all tests in this file as async and ensure a clean database
pytestmark = [pytest.mark.anyio, pytest.mark.usefixtures("setup_test_database")]

async def test_health_check(app_client: AsyncClient):
    """Test the health check endpoint."""
    response = await app_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

async def test_register_and_login(app_client: AsyncClient):
    """Test user registration and subsequent login."""
    # Register a new user
    reg_response = await app_client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "strongpassword"},
    )
    assert reg_response.status_code == 200
    assert reg_response.json()["username"] == "testuser"

    # Login with the new user
    login_response = await app_client.post(
        "/api/v1/auth/login/json",
        json={"username": "testuser", "password": "strongpassword"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["user"]["username"] == "testuser"

async def test_get_ml_prediction_success(app_client: AsyncClient, auth_headers: dict):
    """Test successful ML prediction endpoint."""
    with patch(
        "management_server.services.trading_gateway_client.TradingGatewayClient.get_pair_history",
        new_callable=AsyncMock
    ) as mock_get_history:
        # Arrange
        mock_response = {"data": "some_prediction_data", "signals": [1, 0, -1]}
        mock_get_history.return_value = mock_response

        request_data = {
            "bot_name": "test_bot",
            "pair": "ETH/BTC",
            "timeframe": "5m",
            "strategy": "MyAwesomeStrategy"
        }

        # Act
        response = await app_client.post(
            "/api/v1/advanced/predict",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["bot_name"] == "test_bot"
        assert json_response["predictions"] == mock_response
        mock_get_history.assert_awaited_once()

async def test_get_ml_prediction_gateway_error(app_client: AsyncClient, auth_headers: dict):
    """Test ML prediction endpoint when the gateway returns an error."""
    with patch(
        "management_server.services.trading_gateway_client.TradingGatewayClient.get_pair_history",
        new_callable=AsyncMock
    ) as mock_get_history:
        # Arrange
        mock_get_history.return_value = {"error": "Gateway connection failed"}

        request_data = {
            "bot_name": "failing_bot",
            "pair": "LTC/BTC",
            "timeframe": "1h",
            "strategy": "AnotherStrategy"
        }

        # Act
        response = await app_client.post(
            "/api/v1/advanced/predict",
            json=request_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 500
        # The exact error message might vary, so we check that 'detail' is present
        assert "detail" in response.json()
