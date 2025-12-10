"""
Bot management endpoints. Total: 15 endpoints.
"""

from typing import List, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.dependencies import get_current_active_user
from ...core.feature_flags import feature_flags
from ...database import get_db
from ...db.repositories.bot_repository import BotRepository
from ...db.repositories.freqai_model_repository import FreqAIModelRepository
from ...models.models import (
    BotCreate,
    BotResponse,
    BotUpdate,
    User,
    BotStatusResponse,
)
from ...services.bot_service import BotService
from ...services.trading_gateway_client import (
    TradingGatewayClient,
    get_trading_gateway_client,
)
from ...tools.redis_streams_event_bus import core_streams_event_bus

router = APIRouter()


# --- Dependency Injection ---
def get_bot_service(
    db: AsyncSession = Depends(get_db),
    tg_client: TradingGatewayClient = Depends(get_trading_gateway_client),
) -> BotService:
    """Injects the BotService with its dependencies."""
    bot_repo = BotRepository(db)
    model_repo = FreqAIModelRepository(db)
    return BotService(bot_repo, model_repo, core_streams_event_bus, tg_client)


# --- API Endpoints ---


@router.get("/", response_model=List[BotResponse])
async def get_bots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get a list of all bots with pagination."""
    return await service.get_all_bots(current_user, skip, limit)  # type: ignore


@router.post("/", response_model=BotResponse, status_code=201)
async def create_bot(
    bot_data: BotCreate,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a new bot."""
    return await service.create_bot(bot_data, current_user)


@router.get("/status", response_model=Dict[str, Any])
async def get_all_bots_status(
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get the status of all bots from the Trading Gateway."""
    return await service.get_all_bots_status(current_user)


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get a specific bot by its ID."""
    bot = await service.get_bot_by_id(bot_id, current_user)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_update: BotUpdate,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update an existing bot."""
    bot = await service.update_bot(bot_id, bot_update, current_user)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.delete("/{bot_id}", status_code=204)
async def delete_bot(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a bot."""
    success = await service.delete_bot(bot_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found")
    return None


# --- Bulk Operations ---


@router.post("/start-all", response_model=Dict[str, str])
async def start_all_bots(
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Start all bots for the current user."""
    await service.start_all_bots(current_user)
    return {"message": "Start-all command sent for all bots."}


@router.post("/stop-all", response_model=Dict[str, str])
async def stop_all_bots(
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Stop all bots for the current user."""
    await service.stop_all_bots(current_user)
    return {"message": "Stop-all command sent for all bots."}


@router.post("/restart-all", response_model=Dict[str, str])
async def restart_all_bots(
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Restart all bots for the current user."""
    await service.restart_all_bots(current_user)
    return {"message": "Restart-all command sent for all bots."}


# --- Individual Bot Operations ---


@router.post("/{bot_id}/start", response_model=Dict[str, Any])
async def start_bot(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Start a trading bot via the Trading Gateway."""
    if feature_flags.is_disabled("GLOBAL_TRADING_ENABLED", default=False):
        raise HTTPException(
            status_code=503, detail="Trading is globally disabled by administrators."
        )
    result = await service.start_bot(bot_id, current_user)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{bot_id}/stop", response_model=Dict[str, Any])
async def stop_bot(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Stop a trading bot via the Trading Gateway."""
    result = await service.stop_bot(bot_id, current_user)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{bot_id}/restart", response_model=Dict[str, Any])
async def restart_bot(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Restart a trading bot via the Trading Gateway."""
    result = await service.restart_bot(bot_id, current_user)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{bot_id}/status", response_model=Dict[str, Any])
async def get_bot_status(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get the status of a specific bot from the Trading Gateway."""
    return await service.get_bot_status(bot_id, current_user)


@router.get("/{bot_id}/logs", response_model=Dict[str, Any])
async def get_bot_logs(
    bot_id: int,
    lines: int = Query(100, ge=1, le=1000),
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get logs for a specific bot (placeholder)."""
    return {"bot_id": bot_id, "logs": f"Placeholder for last {lines} lines of logs."}


@router.get("/{bot_id}/config", response_model=Dict[str, Any])
async def get_bot_config(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get the current configuration of a bot."""
    bot = await service.get_bot_by_id(bot_id, current_user)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot.config


@router.put("/{bot_id}/config", response_model=Dict[str, Any])
async def update_bot_config(
    bot_id: int,
    config: Dict[str, Any],
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update the configuration of a bot."""
    bot_update = BotUpdate(config=config)
    bot = await service.update_bot(bot_id, bot_update, current_user)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"message": "Configuration updated successfully", "config": bot.config}


@router.get("/{bot_id}/prediction", response_model=Dict[str, Any])
async def get_bot_prediction(
    bot_id: int,
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get the latest FreqAI prediction for a specific bot."""
    return await service.get_prediction_for_bot(bot_id, current_user)
