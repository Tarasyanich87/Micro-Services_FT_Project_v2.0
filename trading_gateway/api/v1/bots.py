"""
API endpoints for bot management in the Trading Gateway.
"""

from fastapi import APIRouter
from ...services.bot_service import bot_service

router = APIRouter()


@router.post("/{bot_name}/start")
async def start_bot(bot_name: str):
    return await bot_service.start_bot(bot_name)


@router.post("/{bot_name}/stop")
async def stop_bot(bot_name: str):
    return await bot_service.stop_bot(bot_name)


@router.post("/{bot_name}/restart")
async def restart_bot(bot_name: str):
    return await bot_service.restart_bot(bot_name)


@router.get("/{bot_name}/status")
async def get_bot_status(bot_name: str):
    return await bot_service.get_bot_status(bot_name)


@router.get("/status")
async def get_all_bots_status():
    return await bot_service.get_all_bots_status()


@router.get("/{bot_name}/predictions")
async def get_bot_predictions(
    bot_name: str,
    pair: str = "BTC/USDT",
    timeframe: str = "5m",
    strategy: str = "TestStrategy",
):
    """Get FreqAI predictions for a running bot."""
    from ...services.ft_rest_client_service import ft_rest_client_service
    from ...services.freqai_model_handler import freqai_model_handler

    try:
        # Check if bot has FreqAI model cached
        model_path = freqai_model_handler.get_model_path(bot_name)
        if not model_path:
            return {
                "status": "error",
                "bot_name": bot_name,
                "error": "No FreqAI model found for this bot",
            }

        # Get predictions from Freqtrade via REST client
        predictions = await ft_rest_client_service.get_freqai_prediction(
            bot_name=bot_name,
            pair=pair,
            timeframe=timeframe,
            strategy=strategy,
        )

        return {
            "status": "success",
            "bot_name": bot_name,
            "model_path": model_path,
            "predictions": predictions,
            "parameters": {"pair": pair, "timeframe": timeframe, "strategy": strategy},
        }
    except Exception as e:
        return {"status": "error", "bot_name": bot_name, "error": str(e)}
