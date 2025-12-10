import pytest
import asyncio
from fastapi.testclient import TestClient

from ..main import app
from ..services.task_service import TaskService


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
async def task_service():
    """Task service for testing"""
    service = TaskService()
    yield service


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "active_tasks" in data


@pytest.mark.asyncio
async def test_start_backtest(task_service):
    """Test backtest start"""
    result = await task_service.start_backtest(
        strategy_name="TestStrategy",
        config={"timerange": "20240101-20240102"},
        request_id="test",
    )

    assert "task_id" in result
    assert result["status"] == "started"

    # Check task exists
    status = await task_service.get_task_status(result["task_id"])
    assert status["status"] in ["pending", "running", "completed"]


def test_get_active_tasks(client):
    """Test get active tasks endpoint"""
    response = client.get("/tasks")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
