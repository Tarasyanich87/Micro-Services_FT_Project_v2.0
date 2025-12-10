from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from trading_gateway.services.freqai_integration_service import freqai_service

router = APIRouter()

@router.post("/predict", response_model=Dict[str, Any])
async def get_prediction(
    bot_name: str,
    pair: str,
    timeframe: str,
    strategy: str
):
    """
    Get FreqAI prediction for a specific pair from a bot.
    """
    try:
        prediction = await freqai_service.predict(bot_name, pair, timeframe, strategy)
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train", response_model=Dict[str, Any])
async def train_model(
    pairs: List[str],
    start_date: str,
    end_date: str
):
    """
    Trigger a FreqAI model training process.
    """
    try:
        result = await freqai_service.train_model(pairs, start_date, end_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """
    Get performance metrics for the current FreqAI model.
    """
    try:
        metrics = await freqai_service.get_model_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
