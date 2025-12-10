"""
API endpoints for emergency operations.
"""
from fastapi import APIRouter, Depends
from typing import Any, Dict

from ...auth.dependencies import get_current_active_user
from ...models.models import User
from ...services.bot_service import BotService
from .bots import get_bot_service

router = APIRouter()

@router.post("/stop-all", response_model=Dict[str, str])
async def emergency_stop_all_bots(
    service: BotService = Depends(get_bot_service),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Send a high-priority command to immediately terminate all running bot processes.
    """
    await service.emergency_stop_all()
    return {"message": "Emergency stop command sent."}
