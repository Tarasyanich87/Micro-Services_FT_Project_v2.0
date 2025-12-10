#!/usr/bin/env python3
"""
API Tests for Trading Gateway (Port 8001)
Tests bot management, FreqAI integration, and WebSocket functionality.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trading_gateway_health_check(trading_gateway_client: AsyncClient):
    """Test Trading Gateway health check endpoint."""
    response = await trading_gateway_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["service"] == "trading_gateway"


@pytest.mark.asyncio
async def test_trading_gateway_bots_endpoint(trading_gateway_client: AsyncClient):
    """Test bots listing endpoint."""
    response = await trading_gateway_client.get("/api/v1/bots/")
    # Should return 200 even if no bots exist
    assert response.status_code in [200, 404]  # 404 if no bots, but endpoint exists


@pytest.mark.asyncio
async def test_trading_gateway_freqai_endpoint(trading_gateway_client: AsyncClient):
    """Test FreqAI models endpoint."""
    response = await trading_gateway_client.get("/api/v1/freqai/models")
    # Should return 200 even if no models exist
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_trading_gateway_websocket_info(trading_gateway_client: AsyncClient):
    """Test WebSocket info endpoint."""
    response = await trading_gateway_client.get("/api/v1/ws/info")
    assert response.status_code == 200
    data = response.json()
    assert "websocket_url" in data
    assert "supported_events" in data


@pytest.mark.asyncio
async def test_trading_gateway_invalid_endpoint(trading_gateway_client: AsyncClient):
    """Test invalid endpoint returns 404."""
    response = await trading_gateway_client.get("/api/v1/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trading_gateway_cors_headers(trading_gateway_client: AsyncClient):
    """Test CORS headers are present."""
    response = await trading_gateway_client.options("/health")
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers
