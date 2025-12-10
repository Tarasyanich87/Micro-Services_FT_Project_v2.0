"""
Comprehensive monitoring API endpoints.
Provides detailed system monitoring with metrics, health checks, and analytics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from management_server.database import get_db
from management_server.services.monitoring_service import MonitoringService
from management_server.auth.dependencies import (
    get_current_active_user,
    get_current_superuser,
)
from management_server.models.models import User

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


def get_monitoring_service(db: AsyncSession = Depends(get_db)) -> MonitoringService:
    """Dependency to get monitoring service with database session."""
    return MonitoringService(db_session=db)


@router.get("/status", response_model=Dict[str, Any])
async def get_system_status(
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get comprehensive system monitoring status.

    Returns detailed information about:
    - System metrics (CPU, memory, disk usage)
    - Component health (Management Server, Trading Gateway, Redis, Database)
    - Bot statistics (counts, profit, risk metrics)
    - Overall system status

    Requires authenticated user.
    """
    status_data = await service.get_system_status()
    return status_data


@router.get("/health", response_model=Dict[str, Any])
async def get_health_status(
    service: MonitoringService = Depends(get_monitoring_service),
) -> Dict[str, Any]:
    """
    Get basic health status of system components.

    Lightweight endpoint for health checks, returns only component status
    without detailed metrics.

    No authentication required for basic health checks.
    """
    full_status = await service.get_system_status()
    # Return only component health for lightweight health checks
    return {
        "timestamp": full_status.get("timestamp"),
        "overall_status": full_status.get("overall_status"),
        "component_health": full_status.get("component_health"),
    }


@router.get("/test", response_model=Dict[str, Any])
async def test_endpoint() -> Any:
    """Test endpoint without authentication."""
    return {"message": "Test endpoint works", "status": "ok"}


@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics(
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """
    Get detailed system metrics.

    Returns comprehensive system metrics including:
    - CPU, memory, disk usage
    - Network statistics
    - Detailed component information

    Requires superuser privileges.
    """
    full_status = await service.get_system_status()
    return {
        "timestamp": full_status.get("timestamp"),
        "system_metrics": full_status.get("system_metrics"),
        "component_health": full_status.get("component_health"),
        "overall_status": full_status.get("overall_status"),
    }


@router.get("/bots", response_model=Dict[str, Any])
async def get_bot_statistics(
    service: MonitoringService = Depends(get_monitoring_service),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Get bot statistics and analytics.

    Returns information about:
    - Total number of bots
    - Bot status distribution
    - Profit statistics
    - Risk metrics (drawdown)

    Requires authenticated user.
    """
    full_status = await service.get_system_status()
    return {
        "timestamp": full_status.get("timestamp"),
        "bot_statistics": full_status.get("bot_statistics"),
    }
