"""
Analytics endpoints - 6 endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.analytics_service import AnalyticsService
from ...auth.dependencies import get_current_active_user
from ...models.models import User

router = APIRouter(tags=["Analytics"])


@router.get("/test", response_model=Dict[str, Any])
async def test_endpoint():
    """Test endpoint without authentication."""
    return {"message": "Test endpoint works", "status": "ok"}


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db_session=db)


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_analytics(
    bot_id: Optional[int] = None,
    timeframe: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get performance analytics."""
    data = await service.get_performance_analytics(
        bot_id,
        timeframe,
        current_user.id,  # type: ignore[arg-type]
    )
    if data is None:
        raise HTTPException(status_code=404, detail="Analytics data not found")
    return {
        "data": data,
        "timeframe": timeframe,
        "bot_id": bot_id,
        "timestamp": datetime.utcnow(),
    }


@router.get("/profit", response_model=Dict[str, Any])
async def get_profit_analytics(
    bot_id: Optional[int] = None,
    period: str = Query("daily", pattern="^(hourly|daily|weekly|monthly)$"),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get profit analytics."""
    data = await service.get_profit_analytics(bot_id, period, current_user.id)  # type: ignore[arg-type]
    return {"data": data, "period": period, "bot_id": bot_id}


@router.get("/risk", response_model=Dict[str, Any])
async def get_risk_analytics(
    bot_id: Optional[int] = None,
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get risk analytics."""
    data = await service.get_risk_analytics(bot_id, current_user.id)  # type: ignore[arg-type]
    return {"data": data, "bot_id": bot_id}


@router.get("/market", response_model=Dict[str, Any])
async def get_market_analytics(
    symbol: Optional[str] = None,
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get market analytics."""
    data = await service.get_market_analytics(symbol or "bitcoin")  # type: ignore[arg-type]
    return {"data": data, "symbol": symbol or "bitcoin"}


@router.get("/portfolio", response_model=Dict[str, Any])
async def get_portfolio_analytics(
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get portfolio analytics."""
    data = await service.get_portfolio_analytics(current_user.id)  # type: ignore[arg-type]
    return {"data": data}
