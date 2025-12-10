"""
FreqAI service for managing ML models and predictions.
This service acts as a bridge to the Trading Gateway, which communicates with Freqtrade bots.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import Depends

from .trading_gateway_client import TradingGatewayClient, get_trading_gateway_client
from management_server.tasks.tasks import run_freqai_backtest_task

logger = logging.getLogger(__name__)

class FreqAIService:
    """
    Service for interacting with FreqAI models via the Trading Gateway.
    """

    def __init__(self, tg_client: TradingGatewayClient):
        self.tg_client = tg_client

    def create_backtest_task(self, model_id: int, bot_config: dict):
        """
        Queues a FreqAI model backtesting task in Celery.
        """
        task = run_freqai_backtest_task.delay(
            model_id=model_id,
            bot_config=bot_config
        )
        return task

    async def get_prediction(
        self, bot_name: str, pair: str, timeframe: str, strategy: str
    ) -> Dict[str, Any]:
        """
        Get FreqAI predictions for a trading pair by fetching analyzed pair history.
        FreqAI augments the pair history data with its predictions.
        """
        logger.info(f"Getting FreqAI predictions for {pair} from bot {bot_name}")

        # Define a reasonable timerange to fetch, e.g., the last 10 days of data.
        # Freqtrade will provide the last 500 candles by default if not specified.
        timerange = f"{(datetime.now() - timedelta(days=10)).strftime('%Y%m%d')}-"

        return await self.tg_client.get_pair_history(
            bot_name=bot_name,
            pair=pair,
            timeframe=timeframe,
            strategy=strategy,
            timerange=timerange,
        )

    async def get_model_metrics(self, bot_name: str) -> Dict[str, Any]:
        """
        Get metrics for the current ML model.
        NOTE: Freqtrade does not have a standard, dedicated endpoint for this.
        This is a placeholder for a potential future custom implementation.
        """
        logger.warning(
            "get_model_metrics is a placeholder and not yet implemented "
            "as Freqtrade does not expose a standard API for it."
        )
        # In a real scenario, this might scrape logs or read a file produced by the bot.
        return {
            "bot_name": bot_name,
            "status": "not_implemented",
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
        }

# --- FastAPI Dependency ---

def get_freqai_service(
    tg_client: TradingGatewayClient = Depends(get_trading_gateway_client),
) -> FreqAIService:
    """Injects the FreqAIService with its TradingGatewayClient dependency."""
    return FreqAIService(tg_client)
