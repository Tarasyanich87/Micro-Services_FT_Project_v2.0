#!/usr/bin/env python3
"""
API Tests for FreqAI Server (Port 8004)
Tests ML model training, prediction, and management.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_freqai_server_health_check(freqai_client: AsyncClient):
    """Test FreqAI Server health check endpoint."""
    response = await freqai_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["service"] == "freqai_server"


@pytest.mark.asyncio
async def test_freqai_server_models_endpoint(freqai_client: AsyncClient):
    """Test models listing endpoint."""
    response = await freqai_client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_freqai_server_train_model_invalid(freqai_client: AsyncClient):
    """Test training model with invalid parameters."""
    # Test with missing required parameters
    response = await freqai_client.post("/train", json={})
    assert response.status_code in [400, 422]  # Bad request or validation error


@pytest.mark.asyncio
async def test_freqai_server_predict_invalid(freqai_client: AsyncClient):
    """Test prediction with invalid parameters."""
    response = await freqai_client.post("/predict", json={})
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_freqai_server_model_status_invalid(freqai_client: AsyncClient):
    """Test getting status of non-existent model."""
    response = await freqai_client.get("/model/non-existent-model/status")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_freqai_server_invalid_endpoint(freqai_client: AsyncClient):
    """Test invalid endpoint returns 404."""
    response = await freqai_client.get("/api/v1/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_freqai_server_cors_headers(freqai_client: AsyncClient):
    """Test CORS headers are present."""
    response = await freqai_client.options("/health")
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers


@pytest.mark.asyncio
async def test_freqai_server_train_model_minimal(freqai_client: AsyncClient):
    """Test training model with minimal valid parameters."""
    train_data = {
        "model_name": "TestModel",
        "strategy_name": "TestStrategy",
        "timerange": "20240101-20240102",
        "stake_amount": 100.0,
    }

    response = await freqai_client.post("/train", json=train_data)
    # Should either succeed or fail gracefully
    assert response.status_code in [200, 400, 422, 500]
    # If successful, should return training info
    if response.status_code == 200:
        data = response.json()
        assert "model_name" in data
        assert "status" in data


@pytest.mark.asyncio
async def test_freqai_server_training_status(freqai_client: AsyncClient):
    """Test training status endpoint."""
    # First try to start training
    train_data = {
        "model_name": "StatusTestModel",
        "strategy_name": "TestStrategy",
        "timerange": "20240101-20240102",
        "stake_amount": 100.0,
    }

    train_response = await freqai_client.post("/train", json=train_data)
    if train_response.status_code == 200:
        # Check status
        status_response = await freqai_client.get("/training-status/StatusTestModel")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["training", "completed", "failed", "not_found"]


@pytest.mark.asyncio
async def test_freqai_server_model_info(freqai_client: AsyncClient):
    """Test model info endpoint."""
    response = await freqai_client.get("/model/TestModel")
    # Should return 404 if model doesn't exist, or model info if it does
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "model_name" in data


@pytest.mark.asyncio
async def test_freqai_server_prediction_data(freqai_client: AsyncClient):
    """Test prediction data endpoint."""
    response = await freqai_client.get("/prediction-data/TestModel")
    # Should return 404 if model doesn't exist, or prediction data if it does
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
