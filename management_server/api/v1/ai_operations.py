from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
<<<<<<< HEAD

from management_server.services.trading_gateway_client import (
    TradingGatewayClient,
    get_trading_gateway_client
)
from management_server.auth.dependencies import get_current_active_user
from management_server.models.models import User
=======
from management_server.services.trading_gateway_client import trading_gateway_client
from management_server.api.dependencies import get_current_user
from management_server.db.models.user import User
>>>>>>> origin/feat/full-microservice-architecture-with-mcp
from management_server.core.feature_flags import feature_flags

router = APIRouter()

@router.post("/predict", response_model=Dict[str, Any])
async def get_prediction(
    bot_name: str,
    pair: str,
    timeframe: str,
    strategy: str,
<<<<<<< HEAD
    current_user: User = Depends(get_current_active_user),
    tg_client: TradingGatewayClient = Depends(get_trading_gateway_client)
=======
    current_user: User = Depends(get_current_user)
>>>>>>> origin/feat/full-microservice-architecture-with-mcp
):
    """
    Proxy endpoint to get FreqAI prediction from Trading Gateway.
    """
    if feature_flags.is_disabled("AI_PREDICTIONS_ENABLED", default=True):
        raise HTTPException(status_code=503, detail="AI predictions are currently disabled.")
<<<<<<< HEAD
    return await tg_client.predict(bot_name, pair, timeframe, strategy)
=======
    return await trading_gateway_client.predict(bot_name, pair, timeframe, strategy)
>>>>>>> origin/feat/full-microservice-architecture-with-mcp

@router.post("/train", response_model=Dict[str, Any])
async def train_model(
    pairs: List[str],
    start_date: str,
    end_date: str,
<<<<<<< HEAD
    current_user: User = Depends(get_current_active_user),
    tg_client: TradingGatewayClient = Depends(get_trading_gateway_client)
=======
    current_user: User = Depends(get_current_user)
>>>>>>> origin/feat/full-microservice-architecture-with-mcp
):
    """
    Proxy endpoint to trigger model training via Trading Gateway.
    """
<<<<<<< HEAD
    return await tg_client.train_model(pairs, start_date, end_date)

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    current_user: User = Depends(get_current_active_user),
    tg_client: TradingGatewayClient = Depends(get_trading_gateway_client)
):
    """
    Proxy endpoint to get model metrics from Trading Gateway.
    """
    return await tg_client.get_model_metrics()
=======
    return await trading_gateway_client.train_model(pairs, start_date, end_date)

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(current_user: User = Depends(get_current_user)):
    """
    Proxy endpoint to get model metrics from Trading Gateway.
    """
    return await trading_gateway_client.get_model_metrics()
>>>>>>> origin/feat/full-microservice-architecture-with-mcp
