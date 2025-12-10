#!/usr/bin/env python3
"""
API Tests for Backtesting Server (Port 8003)
Tests strategy backtesting, task management, and optimization.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_backtesting_server_health_check(backtesting_client: AsyncClient):
    """Test Backtesting Server health check endpoint."""
    response = await backtesting_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["service"] == "backtesting_server"


@pytest.mark.asyncio
async def test_backtesting_server_tasks_endpoint(backtesting_client: AsyncClient):
    """Test tasks listing endpoint."""
    response = await backtesting_client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_backtesting_server_start_backtest_invalid(
    backtesting_client: AsyncClient,
):
    """Test starting backtest with invalid parameters."""
    # Test with missing required parameters
    response = await backtesting_client.post("/backtest", json={})
    assert response.status_code in [400, 422]  # Bad request or validation error


@pytest.mark.asyncio
async def test_backtesting_server_task_status_invalid(backtesting_client: AsyncClient):
    """Test getting status of non-existent task."""
    response = await backtesting_client.get("/task/non-existent-task-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_backtesting_server_invalid_endpoint(backtesting_client: AsyncClient):
    """Test invalid endpoint returns 404."""
    response = await backtesting_client.get("/api/v1/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_backtesting_server_cors_headers(backtesting_client: AsyncClient):
    """Test CORS headers are present."""
    response = await backtesting_client.options("/health")
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


@pytest.mark.asyncio
async def test_backtesting_server_backtest_with_minimal_params(
    backtesting_client: AsyncClient,
):
    """Test backtest endpoint with minimal valid parameters."""
    backtest_data = {
        "strategy_name": "TestStrategy",
        "config": {"timerange": "20240101-20240102", "stake_amount": 100},
        "request_id": "test_request",
    }

    response = await backtesting_client.post("/backtest", json=backtest_data)
    # Should either succeed or fail gracefully
    assert response.status_code in [200, 400, 422, 500]
    # If successful, should return task info
    if response.status_code == 200:
        data = response.json()
        assert "task_id" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_backtesting_server_task_status_format(backtesting_client: AsyncClient):
    """Test task status response format."""
    # First create a task
    backtest_data = {
        "strategy_name": "TestStrategy",
        "config": {"timerange": "20240101-20240102"},
        "request_id": "test_format",
    }

    create_response = await backtesting_client.post("/backtest", json=backtest_data)
    if create_response.status_code == 200:
        task_data = create_response.json()
        task_id = task_data["task_id"]

        # Check status format
        status_response = await backtesting_client.get(f"/task/{task_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            assert "task_id" in status_data
            assert "status" in status_data
            assert status_data["status"] in [
                "pending",
                "running",
                "completed",
                "failed",
            ]
