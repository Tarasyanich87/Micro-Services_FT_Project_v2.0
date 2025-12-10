"""
Test Celery-based backtesting functionality
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_celery_backtest_workflow(
    management_client: AsyncClient, management_auth_headers: dict
):
    """Test complete backtesting workflow with Celery."""
    # Create backtest request
    backtest_data = {
        "strategy_name": "TestStrategy",
        "timerange": "20240101-20240102",
        "stake_amount": 100.0,
    }

    response = await management_client.post(
        "/api/v1/strategies/backtest",
        json=backtest_data,
        headers=management_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return task info
    assert "id" in data
    assert "celery_task_id" in data
    assert "status" in data
    assert data["status"] in ["queued", "running"]

    task_id = data["id"]
    celery_task_id = data["celery_task_id"]

    # Check task status
    status_response = await management_client.get(
        f"/api/v1/strategies/backtest/results/{task_id}",
        headers=management_auth_headers,
    )

    assert status_response.status_code == 200
    status_data = status_response.json()
    assert "status" in status_data


@pytest.mark.asyncio
async def test_freqai_backtest_workflow(
    management_client: AsyncClient, management_auth_headers: dict
):
    """Test FreqAI backtesting workflow."""
    # First create a FreqAI model
    model_data = {
        "name": "TestFreqAIModel",
        "strategy_name": "FreqaiExampleStrategy",
        "description": "Test model for backtesting",
    }

    response = await management_client.post(
        "/api/v1/freqai/models", json=model_data, headers=management_auth_headers
    )

    if response.status_code == 200:
        model = response.json()

        # Start backtest for the model
        backtest_response = await management_client.post(
            f"/api/v1/freqai/models/{model['id']}/backtest",
            json={"timerange": "20240101-20240102", "stake_amount": 100.0},
            headers=management_auth_headers,
        )

        assert backtest_response.status_code in [200, 202]  # Success or accepted


@pytest.mark.asyncio
async def test_hyperopt_workflow(
    management_client: AsyncClient, management_auth_headers: dict
):
    """Test hyperopt workflow with Celery."""
    hyperopt_data = {
        "strategy_name": "TestStrategy",
        "epochs": 10,
        "spaces": "buy",
        "timerange": "20240101-20240102",
        "stake_amount": 100.0,
    }

    response = await management_client.post(
        "/api/v1/hyperopt", json=hyperopt_data, headers=management_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should return task info
    assert "id" in data
    assert "celery_task_id" in data
    assert "status" in data
