"""
Advanced Trading Features API endpoints, including ML predictions and risk management.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...auth.dependencies import get_current_active_user
from ...models.models import User
from ...services.freqai_service import FreqAIService, get_freqai_service

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic Schemas for Requests ---

class PredictionRequest(BaseModel):
    bot_name: str
    pair: str
    timeframe: str
    strategy: str

class TrainingRequest(BaseModel):
    pairs: List[str]
    start_date: str
    end_date: str

# --- API Endpoints ---

@router.post("/predict", tags=["FreqAI"])
async def get_ml_prediction(
    request: PredictionRequest,
    current_user: User = Depends(get_current_active_user),
    freqai_service: FreqAIService = Depends(get_freqai_service),
):
    """Get ML predictions for a trading pair from a specific bot."""
    try:
        predictions = await freqai_service.get_prediction(
            bot_name=request.bot_name,
            pair=request.pair,
            timeframe=request.timeframe,
            strategy=request.strategy,
        )
        if "error" in predictions:
            raise HTTPException(status_code=400, detail=predictions["error"])

        return {
            "bot_name": request.bot_name,
            "pair": request.pair,
            "predictions": predictions,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception(f"Error getting ML prediction for {request.pair}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model-metrics", tags=["FreqAI"])
async def get_model_metrics(
    bot_name: str,
    current_user: User = Depends(get_current_active_user),
    freqai_service: FreqAIService = Depends(get_freqai_service),
):
    """Get performance metrics of the current FreqAI model."""
    try:
        metrics = await freqai_service.get_model_metrics(bot_name)
        if "error" in metrics:
            raise HTTPException(status_code=400, detail=metrics["error"])
        return metrics
    except Exception as e:
        logger.exception(f"Error getting model metrics for {bot_name}")
        raise HTTPException(status_code=500, detail=str(e))
