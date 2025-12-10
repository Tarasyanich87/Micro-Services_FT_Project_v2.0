"""
Manages the lifecycle of Freqtrade bot processes.
"""

import asyncio
import base64
import json
import logging
import os
import socket
import subprocess
from pathlib import Path
from typing import Dict, Any

from management_server.tools.redis_streams_event_bus import RedisStreamsEventBus

logger = logging.getLogger(__name__)


class BotProcessManager:
    """
    Handles starting, stopping, and monitoring Freqtrade bot processes.
    """

    def __init__(self, event_bus: RedisStreamsEventBus):
        self.event_bus = event_bus
        self.running_bots: Dict[str, subprocess.Popen] = {}
        self.bot_configs: Dict[str, Dict[str, Any]] = {}
        self.base_bot_dir = Path("bots_data")
        self.base_bot_dir.mkdir(exist_ok=True)

        # Lazy import to avoid circular dependencies
        self._freqai_handler = None

    @property
    def freqai_handler(self):
        """Lazy load FreqAI model handler."""
        if self._freqai_handler is None:
            from .freqai_model_handler import freqai_model_handler

            self._freqai_handler = freqai_model_handler
        return self._freqai_handler

    def _find_free_port(self) -> int:
        """Finds a free port on the host machine."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))  # Bind to a free port
            return s.getsockname()[1]

    async def _handle_freqai_model(
        self,
        bot_name: str,
        bot_config: Dict[str, Any],
        freqai_model_data: Dict[str, Any],
    ):
        """Handle FreqAI model using the FreqAIModelHandler."""
        try:
            # Store model using FreqAIModelHandler
            model_path = await self.freqai_handler.store_model_for_bot(
                bot_name, freqai_model_data
            )

            logger.info(f"FreqAI model stored for bot {bot_name}: {model_path}")

            # Update bot config to point to the model
            if "freqai" not in bot_config:
                bot_config["freqai"] = {}

            bot_config["freqai"]["enabled"] = True
            bot_config["freqai"]["model_path"] = model_path

        except Exception as e:
            logger.error(f"Failed to handle FreqAI model for bot {bot_name}: {e}")
            raise

    async def handle_start_bot_command(self, command_data: Dict[str, Any]):
        """Receives a START_BOT command and initiates the bot process."""
        bot_name = command_data.get("bot_name")
        bot_config = command_data.get("bot_config")
        freqai_model_data = command_data.get("freqai_model")

        if not bot_name or not isinstance(bot_config, dict):
            logger.error(f"Invalid START_BOT command received: {command_data}")
            await self.event_bus.publish(
                "mcp_events",
                {
                    "bot_name": bot_name or "unknown",
                    "status": "error",
                    "error_message": "Invalid command data",
                },
                event_type="BOT_START_FAILED",
            )
            return

        if bot_name in self.running_bots:
            logger.warning(f"Bot '{bot_name}' is already running.")
            return

        logger.info(f"Starting bot '{bot_name}'...")
        bot_dir = self.base_bot_dir / bot_name
        bot_dir.mkdir(exist_ok=True)

        if freqai_model_data:
            await self._handle_freqai_model(bot_name, bot_config, freqai_model_data)

        port = self._find_free_port()

        # Use user-defined API settings or set defaults
        api_server_config = bot_config.get("api_server", {})
        api_server_config.update(
            {
                "enabled": True,
                "listen_ip_address": "0.0.0.0",
                "listen_port": port,
                "username": api_server_config.get("username", "user"),
                "password": api_server_config.get("password", "password"),
            }
        )
        bot_config["api_server"] = api_server_config

        config_path = bot_dir / "config.json"
        with open(config_path, "w") as f:
            json.dump(bot_config, f, indent=4)

        self.bot_configs[bot_name] = bot_config

        try:
            command = [
                "freqtrade",
                "trade",
                "--config",
                str(config_path),
                "--db-url",
                f"sqlite:///{bot_dir / 'tradesv3.sqlite'}",
            ]

            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            self.running_bots[bot_name] = process
            logger.info(
                f"Bot '{bot_name}' started with PID {process.pid} on port {port}."
            )

            await self.event_bus.publish(
                "mcp_events",
                {
                    "bot_name": bot_name,
                    "status": "running",
                    "pid": process.pid,
                    "port": port,
                },
                event_type="BOT_STARTED",
            )

        except Exception as e:
            logger.error(f"Failed to start bot '{bot_name}': {e}")
            await self.event_bus.publish(
                "mcp_events",
                {"bot_name": bot_name, "status": "error", "error_message": str(e)},
                event_type="BOT_START_FAILED",
            )

    async def handle_stop_bot_command(self, command_data: Dict[str, Any]):
        bot_name = command_data.get("bot_name")
        if bot_name not in self.running_bots:
            logger.warning(f"Received stop command for non-running bot '{bot_name}'.")
            return

        logger.info(f"Stopping bot '{bot_name}'...")
        process = self.running_bots[bot_name]
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            logger.warning(f"Bot '{bot_name}' did not terminate gracefully. Killing.")
            process.kill()

        del self.running_bots[bot_name]
        del self.bot_configs[bot_name]

        # Cleanup FreqAI models for this bot
        await self.freqai_handler.cleanup_bot_models(bot_name)

        logger.info(f"Bot '{bot_name}' stopped.")

        await self.event_bus.publish(
            "mcp_events",
            {"bot_name": bot_name, "status": "stopped"},
            event_type="BOT_STOPPED",
        )

    async def handle_restart_bot_command(self, command_data: Dict[str, Any]):
        bot_name = command_data.get("bot_name")
        logger.info(f"Restarting bot '{bot_name}'...")
        if bot_name in self.running_bots:
            await self.handle_stop_bot_command({"bot_name": bot_name})
            await asyncio.sleep(5)

        await self.handle_start_bot_command(command_data)

    async def handle_emergency_stop_all_command(self):
        logger.warning("Executing EMERGENCY STOP ALL! Terminating all processes...")
        running_bot_names = list(self.running_bots.keys())

        for bot_name in running_bot_names:
            process = self.running_bots[bot_name]
            process.kill()
            del self.running_bots[bot_name]
            del self.bot_configs[bot_name]
            logger.info(f"Process for bot '{bot_name}' (PID: {process.pid}) killed.")

            await self.event_bus.publish(
                "mcp_events",
                {"bot_name": bot_name, "status": "stopped", "reason": "emergency_stop"},
                event_type="BOT_STOPPED",
            )

    def get_bot_logs(self, bot_name: str) -> str:
        """Get logs for a specific bot."""
        try:
            if bot_name in self.running_bots:
                # For now, return basic status
                return f"Bot {bot_name} is running (PID: {self.running_bots[bot_name].pid})"
            else:
                return f"Bot {bot_name} is not running"
        except Exception as e:
            logger.error(f"Failed to get logs for bot {bot_name}: {e}")
            return f"Error getting logs: {str(e)}"

    def get_bot_config(self, bot_name: str) -> Dict[str, Any]:
        """Get configuration for a specific bot."""
        try:
            if bot_name in self.bot_configs:
                return self.bot_configs[bot_name]
            else:
                return {"error": f"Configuration for bot {bot_name} not found"}
        except Exception as e:
            logger.error(f"Failed to get config for bot {bot_name}: {e}")
            return {"error": str(e)}
        logger.warning("All bot processes have been terminated.")
