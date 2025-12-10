"""
Test multi-service fixtures from conftest.py
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_management_client_fixture(management_client: AsyncClient):
    """Test that management client fixture works."""
    response = await management_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_trading_gateway_client_fixture(trading_gateway_client: AsyncClient):
    """Test that trading gateway client fixture works."""
    response = await trading_gateway_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_management_auth_headers(management_auth_headers: dict):
    """Test that auth headers fixture works."""
    assert "Authorization" in management_auth_headers
    assert management_auth_headers["Authorization"].startswith("Bearer ")


def test_test_config_fixture(test_config: dict):
    """Test that test config fixture works."""
    assert "management_server_url" in test_config
    assert "trading_gateway_url" in test_config
    assert "test_user" in test_config
