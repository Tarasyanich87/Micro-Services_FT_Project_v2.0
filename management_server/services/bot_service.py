"""
Service for bot management.
Orchestrates bot operations by interacting with the database and publishing commands to a Redis Stream.
"""

import base64
import logging
import os
from typing import Any, Dict, List, Optional

from management_server.db.repositories.bot_repository import BotRepository
from management_server.db.repositories.freqai_model_repository import (
    FreqAIModelRepository,
)
from management_server.models.models import Bot, BotCreate, BotUpdate, BotStatus, User
from management_server.tools.redis_streams_event_bus import RedisStreamsEventBus
from management_server.services.trading_gateway_client import TradingGatewayClient
from management_server.services.freqtrade_client import FreqtradeClient


logger = logging.getLogger(__name__)


class BotService:
    def __init__(
        self,
        bot_repo: BotRepository,
        model_repo: FreqAIModelRepository,
        event_bus: RedisStreamsEventBus,
        tg_client: TradingGatewayClient,
    ):
        self.bot_repo = bot_repo
        self.model_repo = model_repo
        self.event_bus = event_bus
        self.tg_client = tg_client

    async def get_all_bots(self, user: User, skip: int, limit: int) -> List[Bot]:
        """Get all bots for a user with pagination."""
        return await self.bot_repo.get_all(user.id, skip, limit)  # type: ignore

    async def create_bot(self, bot_data: BotCreate, user: User) -> Bot:
        """Create a new bot."""
        # Generate full Freqtrade config from bot data
        full_config = self._generate_freqtrade_config(bot_data)
        bot_data.config = full_config
        return await self.bot_repo.create(bot_data, user.id)  # type: ignore

    def _generate_freqtrade_config(self, bot_data: BotCreate) -> Dict[str, Any]:
        """Generate a complete Freqtrade configuration from bot data."""
        config = {
            "trading_mode": "spot",
            "dry_run": True,  # Always start in dry-run mode for safety
            "timeframe": "5m",
            "max_open_trades": bot_data.max_open_trades,
            "stake_currency": bot_data.stake_currency,
            "stake_amount": bot_data.stake_amount,
            "exchange": {
                "name": bot_data.exchange,
                "key": "",  # Will be set by user later
                "secret": "",  # Will be set by user later
                "pair_whitelist": ["BTC/USDT", "ETH/USDT"],  # Default pairs
                "ccxt_config": {},
            },
            "pairlists": [{"method": "StaticPairList"}],
            "strategy": bot_data.strategy_name,
            "exit_pricing": {
                "price_side": "same",
                "use_order_book": True,
                "order_book_top": 1,
                "price_last_balance": 0.0,
            },
            "entry_pricing": {
                "price_side": "same",
                "use_order_book": True,
                "order_book_top": 1,
                "price_last_balance": 0.0,
                "check_depth_of_market": {"enabled": False, "bids_to_ask_delta": 1},
            },
        }

        # Add FreqAI config if needed
        if bot_data.freqai_model_id:
            config["freqai"] = {
                "enabled": True,
                "identifier": f"freqai_{bot_data.name}",
            }

        return config

    async def get_bot_by_id(self, bot_id: int, user: User) -> Optional[Bot]:
        """Get a bot by its ID."""
        return await self.bot_repo.get_by_id(bot_id, user.id)  # type: ignore

    async def update_bot(
        self, bot_id: int, bot_data: BotUpdate, user: User
    ) -> Optional[Bot]:
        """Update a bot and set restart_required flag if it's running."""
        bot = await self.bot_repo.get_by_id(bot_id, user.id)  # type: ignore
        if not bot:
            return None

        if bot.status == "running":  # type: ignore
            bot_data.restart_required = True

        return await self.bot_repo.update(bot_id, bot_data, user.id)  # type: ignore

    async def delete_bot(self, bot_id: int, user: User) -> bool:
        """Delete a bot."""
        return await self.bot_repo.delete(bot_id, user.id)  # type: ignore

    async def _prepare_start_command(self, bot: Bot, user: User) -> Dict[str, Any]:
        """Helper to prepare the data for START_BOT and RESTART_BOT commands."""
        logger.info(
            f"User {user.username} is preparing to start/restart bot {bot.name} (ID: {bot.id})"
        )

        bot_config = bot.config if isinstance(bot.config, dict) else {}
        command_data = {
            "bot_name": bot.name,
            "bot_config": bot_config,
            "freqai_model": None,  # Default to None
        }

        if bot.freqai_model_id:  # type: ignore
            logger.info(
                f"Bot {bot.name} has FreqAI model ID {bot.freqai_model_id} attached. Preparing model for deployment."
            )
            model = await self.model_repo.get_by_id(bot.freqai_model_id, user.id)  # type: ignore
            if model and os.path.exists(model.file_path):  # type: ignore
                try:
                    with open(model.file_path, "rb") as f:  # type: ignore
                        model_content = f.read()

                    command_data["freqai_model"] = {
                        "filename": os.path.basename(model.file_path),  # type: ignore
                        "content_b64": base64.b64encode(model_content).decode("utf-8"),
                    }
                    logger.info(
                        f"Successfully read and encoded FreqAI model '{model.name}' for deployment."
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to read or encode FreqAI model file for bot {bot.name}: {e}"
                    )
            else:
                logger.warning(
                    f"FreqAI model with ID {bot.freqai_model_id} not found or file does not exist. Starting bot without a model."
                )

        return command_data

    async def start_bot(self, bot_id: int, user: User) -> Dict[str, Any]:
        """Publish a command to start a bot."""
        bot = await self.get_bot_by_id(bot_id, user)
        if not bot:
            return {
                "error": "Bot not found or you do not have permission to access it."
            }

        command_data = await self._prepare_start_command(bot, user)

        await self.event_bus.publish(
            stream_name="mcp_commands", event_data=command_data, event_type="START_BOT"
        )

        # Отправка WebSocket события для real-time обновлений
        await self.event_bus.publish(
            stream_name="bot_events",
            event_data={
                "bot_id": bot_id,
                "bot_name": bot.name,
                "user_id": user.id,
                "action": "starting",
                "timestamp": "2025-12-08T22:30:00Z",
            },
            event_type="BOT_STARTING",
        )

        await self.bot_repo.update_bot_status(bot_id, BotStatus.STARTING)  # type: ignore
        return {"status": "start_command_sent", "bot_name": bot.name}

    async def stop_bot(self, bot_id: int, user: User) -> Dict[str, Any]:
        """Publish a command to stop a bot."""
        bot = await self.get_bot_by_id(bot_id, user)
        if not bot:
            return {
                "error": "Bot not found or you do not have permission to access it."
            }

        logger.info(
            f"User {user.username} is requesting to stop bot {bot.name} (ID: {bot_id})"
        )

        command_data = {"bot_name": bot.name}
        await self.event_bus.publish(
            stream_name="mcp_commands", event_data=command_data, event_type="STOP_BOT"
        )

        # Отправка WebSocket события для real-time обновлений
        await self.event_bus.publish(
            stream_name="bot_events",
            event_data={
                "bot_id": bot_id,
                "bot_name": bot.name,
                "user_id": user.id,
                "action": "stopping",
                "timestamp": "2025-12-08T22:30:00Z",
            },
            event_type="BOT_STOPPING",
        )

        await self.bot_repo.update_bot_status(bot_id, "stopping")
        return {"status": "stop_command_sent", "bot_name": bot.name}

    async def restart_bot(self, bot_id: int, user: User) -> Dict[str, Any]:
        """Publish a command to restart a bot."""
        bot = await self.get_bot_by_id(bot_id, user)
        if not bot:
            return {
                "error": "Bot not found or you do not have permission to access it."
            }

        command_data = await self._prepare_start_command(bot, user)

        await self.event_bus.publish(
            stream_name="mcp_commands",
            event_data=command_data,
            event_type="RESTART_BOT",
        )

        # Отправка WebSocket события для real-time обновлений
        await self.event_bus.publish(
            stream_name="bot_events",
            event_data={
                "bot_id": bot_id,
                "bot_name": bot.name,
                "user_id": user.id,
                "action": "restarting",
                "timestamp": "2025-12-08T22:30:00Z",
            },
            event_type="BOT_RESTARTING",
        )

        await self.bot_repo.update(
            bot_id,
            BotUpdate(restart_required=False, status=BotStatus.STARTING),
            user.id,  # type: ignore
        )
        return {"status": "restart_command_sent", "bot_name": bot.name}

    # ... (rest of the bulk and status methods remain the same)
    async def start_all_bots(self, user: User):
        """Publish a start command for all of a user's bots."""
        bots = await self.get_all_bots(user, 0, 1000)  # Assuming max 1000 bots
        for bot in bots:
            await self.start_bot(bot.id, user)  # type: ignore

    async def stop_all_bots(self, user: User):
        """Publish a stop command for all of a user's bots."""
        bots = await self.get_all_bots(user, 0, 1000)
        for bot in bots:
            await self.stop_bot(bot.id, user)  # type: ignore

    async def restart_all_bots(self, user: User):
        """Publish a restart command for all of a user's bots."""
        bots = await self.get_all_bots(user, 0, 1000)
        for bot in bots:
            await self.restart_bot(bot.id, user)  # type: ignore

    async def emergency_stop_all(self):
        """Publish a single, high-priority command to stop all processes immediately."""
        logger.warning("Broadcasting EMERGENCY_STOP_ALL command!")
        await self.event_bus.publish(
            stream_name="mcp_commands",
            event_data={},  # No specific data needed, it's a broadcast
            event_type="EMERGENCY_STOP_ALL",
        )

    async def get_bot_status(self, bot_id: int, user: User) -> Dict[str, Any]:
        """Get the status of a specific bot directly from the Trading Gateway."""
        bot = await self.get_bot_by_id(bot_id, user)
        if not bot:
            return {"error": "Bot not found"}
        return await self.tg_client.get_bot_status(bot.name)  # type: ignore

    async def get_all_bots_status(self, user: User) -> Dict[str, Any]:
        """Get the status of all bots directly from the Trading Gateway."""
        return await self.tg_client.get_all_bots_status()

    async def get_prediction_for_bot(self, bot_id: int, user: User) -> Dict[str, Any]:
        """Get the latest FreqAI prediction for a specific bot."""
        bot = await self.get_bot_by_id(bot_id, user)
        if not (bot and bot.status == "running" and bot.port and bot.freqai_model_id):  # type: ignore
            return {
                "prediction": "N/A",
                "confidence": 0.0,
                "reason": "Bot not running or not a FreqAI bot.",
            }

        pair_whitelist = bot.config.get("pair_whitelist", [])
        if not pair_whitelist:
            return {
                "prediction": "N/A",
                "confidence": 0.0,
                "reason": "Bot has no pairs in whitelist.",
            }

        api_settings = bot.config.get("api_server", {})
        username = api_settings.get("username", "user")  # Default to 'user'
        password = api_settings.get("password", "password")  # Default to 'password'

        client = FreqtradeClient(f"http://localhost:{bot.port}", username, password)

        try:
            pair = pair_whitelist[0]
            timeframe = bot.config.get("timeframe", "5m")
            strategy = bot.strategy_name

            history = await client.get_pair_history(pair, timeframe, strategy)  # type: ignore

            if not history.get("data"):
                return {
                    "prediction": "N/A",
                    "confidence": 0.0,
                    "reason": "No history data returned.",
                }

            last_candle = history["data"][-1]
            columns = history["columns"]

            prediction = "neutral"
            confidence = 0.0

            long_signal_idx = (
                columns.index("&--DI_long") if "&--DI_long" in columns else -1
            )
            short_signal_idx = (
                columns.index("&--DI_short") if "&--DI_short" in columns else -1
            )

            if long_signal_idx != -1 and last_candle[long_signal_idx] > 0:
                prediction = "long"
                conf_idx = (
                    columns.index("&--confidence_long")
                    if "&--confidence_long" in columns
                    else -1
                )
                if conf_idx != -1:
                    confidence = last_candle[conf_idx]

            elif short_signal_idx != -1 and last_candle[short_signal_idx] > 0:
                prediction = "short"
                conf_idx = (
                    columns.index("&--confidence_short")
                    if "&--confidence_short" in columns
                    else -1
                )
                if conf_idx != -1:
                    confidence = last_candle[conf_idx]

            return {"prediction": prediction, "confidence": round(confidence, 4)}

        except Exception as e:
            logger.error(f"Error getting prediction for bot {bot.name}: {e}")
            return {"prediction": "Error", "confidence": 0.0, "reason": str(e)}
        finally:
            await client.close()
