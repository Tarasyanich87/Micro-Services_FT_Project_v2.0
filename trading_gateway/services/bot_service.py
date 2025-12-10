"""
Bot service for Trading Gateway.
Provides high-level bot management operations.
"""

import asyncio
import logging
from typing import Dict, Any

from .bot_process_manager import BotProcessManager
from .freqai_integration_service import FreqAIIntegrationService
from .ft_rest_client_service import FtRestClientService
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus

logger = logging.getLogger(__name__)

# Global instances
bot_process_manager = BotProcessManager(mcp_streams_event_bus)
freqai_service = FreqAIIntegrationService()
ft_client_service = FtRestClientService()


class BotService:
    """
    High-level bot service that coordinates between different components.
    """

    async def start_bot(self, bot_name: str) -> Dict[str, Any]:
        """Start a bot with FreqAI integration."""
        try:
            logger.info(f"Starting bot: {bot_name}")

            # Send start command through event bus
            command_data = {"bot_name": bot_name}
            await mcp_streams_event_bus.publish(
                "bot_commands", command_data, "START_BOT"
            )

            return {
                "status": "success",
                "message": f"Bot {bot_name} start command sent",
            }
        except Exception as e:
            logger.error(f"Failed to start bot {bot_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def stop_bot(self, bot_name: str) -> Dict[str, Any]:
        """Stop a bot."""
        try:
            logger.info(f"Stopping bot: {bot_name}")

            # Send stop command through event bus
            command_data = {"bot_name": bot_name}
            await mcp_streams_event_bus.publish(
                "bot_commands", command_data, "STOP_BOT"
            )

            # Cleanup FreqAI models (additional cleanup in case needed)
            await self._cleanup_freqai_models(bot_name)

            return {"status": "success", "message": f"Bot {bot_name} stop command sent"}
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def restart_bot(self, bot_name: str) -> Dict[str, Any]:
        """Restart a bot."""
        try:
            logger.info(f"Restarting bot: {bot_name}")

            # Stop first
            await self.stop_bot(bot_name)
            await asyncio.sleep(2)  # Wait for clean shutdown

            # Then start
            return await self.start_bot(bot_name)
        except Exception as e:
            logger.error(f"Failed to restart bot {bot_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_bot_status(self, bot_name: str) -> Dict[str, Any]:
        """Get bot status."""
        try:
            logger.info(f"Getting status for bot: {bot_name}")

            # Check if bot is running in process manager
            if bot_name in bot_process_manager.running_bots:
                status = "running"
                pid = bot_process_manager.running_bots[bot_name].pid
            else:
                status = "stopped"
                pid = None

            return {
                "status": "success",
                "bot_name": bot_name,
                "bot_status": status,
                "pid": pid,
            }
        except Exception as e:
            logger.error(f"Failed to get status for bot {bot_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_bot_logs(self, bot_name: str) -> Dict[str, Any]:
        """Get bot logs."""
        try:
            logger.info(f"Getting logs for bot: {bot_name}")

            # Get logs from process manager
            logs = bot_process_manager.get_bot_logs(bot_name)

            return {"status": "success", "bot_name": bot_name, "logs": logs}
        except Exception as e:
            logger.error(f"Failed to get logs for bot {bot_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_bot_config(self, bot_name: str) -> Dict[str, Any]:
        """Get bot configuration."""
        try:
            logger.info(f"Getting config for bot: {bot_name}")

            # Get config from process manager
            config = bot_process_manager.get_bot_config(bot_name)

            return {"status": "success", "bot_name": bot_name, "config": config}
        except Exception as e:
            logger.error(f"Failed to get config for bot {bot_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_all_bots_status(self) -> Dict[str, Any]:
        """Get status of all bots."""
        try:
            logger.info("Getting status for all bots")

            results = {}
            for bot_name in bot_process_manager.running_bots.keys():
                status = await self.get_bot_status(bot_name)
                results[bot_name] = status

            return {"status": "success", "bots": results}
        except Exception as e:
            logger.error(f"Failed to get all bots status: {e}")
            return {"status": "error", "message": str(e)}

    async def _cleanup_freqai_models(self, bot_name: str):
        """Cleanup FreqAI models for a bot."""
        try:
            from .freqai_model_handler import freqai_model_handler

            await freqai_model_handler.cleanup_bot_models(bot_name)
            logger.info(f"Cleaned up FreqAI models for bot {bot_name}")
        except Exception as e:
            logger.error(f"Failed to cleanup FreqAI models for bot {bot_name}: {e}")
            # Don't raise exception - cleanup failure shouldn't stop bot shutdown


# Global bot service instance
bot_service = BotService()
