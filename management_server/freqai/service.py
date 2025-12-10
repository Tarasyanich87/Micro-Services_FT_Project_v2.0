"""
Service for interacting with FreqAI instances.
"""

import logging
from typing import Dict, Any, Optional

from ..services.trading_gateway_client import TradingGatewayClient
from ..models.models import Bot
from fastapi import Depends

logger = logging.getLogger(__name__)

class FreqAIService:
    """
    Service for managing and interacting with FreqAI models and bots.
    """

    def __init__(self, trading_gateway_client: TradingGatewayClient = Depends()):
        self.trading_gateway_client = trading_gateway_client

    async def get_freqai_status(self, bot: Bot) -> Dict[str, Any]:
        """
        Get the status of the FreqAI instance for a given bot.
        """
        logger.info(f"Getting FreqAI status for bot: {bot.name}")
        return await self.trading_gateway_client.get_freqai_status(bot.name)

    async def start_freqai(self, bot: Bot) -> Dict[str, Any]:
        """
        Start the FreqAI instance for a given bot.
        """
        logger.info(f"Starting FreqAI for bot: {bot.name}")
        return await self.trading_gateway_client.start_freqai(bot.name)

    async def stop_freqai(self, bot: Bot) -> Dict[str, Any]:
        """
        Stop the FreqAI instance for a given bot.
        """
        logger.info(f"Stopping FreqAI for bot: {bot.name}")
        return await self.trading_gateway_client.stop_freqai(bot.name)

    async def get_predictions(self, bot: Bot, pair: str, timeframe: str, strategy: str, freqaimodel: str) -> Dict[str, Any]:
        """
        Get predictions from the FreqAI instance for a given bot and pair.
        """
        logger.info(f"Getting predictions for bot: {bot.name}, pair: {pair}")
        return await self.trading_gateway_client.get_freqai_prediction(bot.name, pair, timeframe, strategy, freqaimodel)

    async def start_backtest(self, bot: Bot, strategy: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a backtest for a given bot and strategy.
        """
        logger.info(f"Starting backtest for bot: {bot.name}, strategy: {strategy}")
        # This will be replaced with a real call to the trading_gateway_client
        return {"status": "backtest_started", "bot_name": bot.name, "strategy": strategy}

    async def get_backtest_results(self, bot: Bot, backtest_id: str) -> Dict[str, Any]:
        """
        Get the results of a backtest.
        """
        logger.info(f"Getting backtest results for bot: {bot.name}, backtest_id: {backtest_id}")
        # This will be replaced with a real call to the trading_gateway_client
        return {"results": "...", "bot_name": bot.name, "backtest_id": backtest_id}
