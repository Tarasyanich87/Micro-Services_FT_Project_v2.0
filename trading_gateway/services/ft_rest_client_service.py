"""
Централизованный FtRestClient Service для управления всеми Freqtrade ботами.
Обеспечивает единый интерфейс для Core Server и MCP Bridge.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from contextlib import asynccontextmanager
import aiohttp
import json
from datetime import datetime, timedelta
from management_server.tools.redis_streams_event_bus import (
    mcp_streams_event_bus as event_bus,
)

logger = logging.getLogger(__name__)


@dataclass
class BotConnection:
    """Конфигурация подключения к боту"""

    name: str
    url: str
    ui_url: str
    username: str
    password: str
    session: Optional[aiohttp.ClientSession] = None
    last_health_check: Optional[datetime] = None
    is_healthy: bool = False
    retry_count: int = 0
    max_retries: int = 3


class FtRestClientService:
    """
    Централизованный сервис для управления Freqtrade ботами.
    Используется Core Server и MCP Bridge для всех операций с ботами.
    """

    def __init__(self):
        self.connections: Dict[str, BotConnection] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
        self.event_bus = event_bus

    async def initialize(self, bot_configs: Dict[str, Dict[str, Any]]) -> bool:
        """Инициализация сервиса с конфигурациями ботов"""
        async with self._lock:
            try:
                logger.info(
                    f"Initializing FtRestClient Service with {len(bot_configs)} bots"
                )

                for bot_name, config in bot_configs.items():
                    connection = BotConnection(
                        name=bot_name,
                        url=config["api_url"],
                        ui_url=config.get(
                            "ui_url", f"http://localhost:{8080 + len(self.connections)}"
                        ),  # Default ui_url
                        username=config.get("api_username", "freqtrade"),
                        password=config.get("api_password", "supersecurepassword"),
                    )
                    self.connections[bot_name] = connection

                # Создание сессий для всех ботов
                await self._create_sessions()

                self._initialized = True
                logger.info("FtRestClient Service initialized successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to initialize FtRestClient Service: {e}")
                return False

    async def _create_sessions(self):
        """Создание HTTP сессий для всех ботов"""
        for connection in self.connections.values():
            if connection.session is None or connection.session.closed:
                connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
                timeout = aiohttp.ClientTimeout(total=30, connect=10)

                connection.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    auth=aiohttp.BasicAuth(connection.username, connection.password),
                )

    async def _ensure_session(self, bot_name: str) -> Optional[aiohttp.ClientSession]:
        """Обеспечение активной сессии для бота"""
        if bot_name not in self.connections:
            logger.error(f"Bot {bot_name} not configured")
            return None

        connection = self.connections[bot_name]

        # Проверка здоровья сессии
        if connection.session is None or connection.session.closed:
            await self._create_sessions()

        return connection.session

    async def _make_request(
        self,
        bot_name: str,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Универсальный метод для HTTP запросов к боту"""

        session = await self._ensure_session(bot_name)
        if not session:
            return {"error": f"No session available for bot {bot_name}"}

        url = f"{self.connections[bot_name].url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            async with session.request(
                method, url, json=data if data else None
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(
                        f"API error for bot {bot_name}: {response.status} {error_text}"
                    )
                    return {
                        "error": f"API request failed with status {response.status}",
                        "details": error_text,
                    }
                result = await response.json()

            # Обновление статуса здоровья
            self.connections[bot_name].last_health_check = datetime.now()
            self.connections[bot_name].is_healthy = True
            self.connections[bot_name].retry_count = 0

            return result

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error for bot {bot_name}, endpoint {endpoint}: {e}")
            await self._handle_connection_error(bot_name)
            return {"error": f"Connection failed: {str(e)}"}

        except Exception as e:
            logger.error(f"Unexpected error for bot {bot_name}: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

    async def _handle_connection_error(self, bot_name: str):
        """Обработка ошибок подключения"""
        connection = self.connections[bot_name]
        connection.retry_count += 1
        connection.is_healthy = False

        if connection.retry_count >= connection.max_retries:
            logger.warning(f"Bot {bot_name} reached max retries, marking as unhealthy")

    # === ОСНОВНЫЕ МЕТОДЫ УПРАВЛЕНИЯ БОТАМИ ===

    async def start_bot(self, bot_name: str) -> Dict[str, Any]:
        """Запуск бота"""
        logger.info(f"Starting bot: {bot_name}")
        result = await self._make_request(bot_name, "POST", "/api/v1/status/start")
        await self.event_bus.publish(
            "bot_events", {"bot_name": bot_name, "result": result}, "bot_started"
        )
        return result

    async def stop_bot(self, bot_name: str) -> Dict[str, Any]:
        """Остановка бота"""
        logger.info(f"Stopping bot: {bot_name}")
        return await self._make_request(bot_name, "POST", "/api/v1/status/stop")

    async def restart_bot(self, bot_name: str) -> Dict[str, Any]:
        """Перезапуск бота"""
        logger.info(f"Restarting bot: {bot_name}")
        stop_result = await self.stop_bot(bot_name)
        if "error" in stop_result:
            return stop_result

        await asyncio.sleep(2)
        return await self.start_bot(bot_name)

    async def get_bot_status(self, bot_name: str) -> Dict[str, Any]:
        """Получение статуса бота"""
        return await self._make_request(bot_name, "GET", "/api/v1/status")

    async def get_bot_profit(self, bot_name: str) -> Dict[str, Any]:
        """Получение данных о прибыли бота"""
        return await self._make_request(bot_name, "GET", "/api/v1/profit")

    async def get_bot_balance(self, bot_name: str) -> Dict[str, Any]:
        """Получение баланса бота"""
        return await self._make_request(bot_name, "GET", "/api/v1/balance")

    async def get_open_trades(self, bot_name: str) -> Dict[str, Any]:
        """Получение открытых сделок"""
        return await self._make_request(bot_name, "GET", "/api/v1/status")

    async def force_exit_trade(self, bot_name: str, trade_id: str) -> Dict[str, Any]:
        """Принудительное закрытие сделки"""
        return await self._make_request(
            bot_name, "POST", f"/api/v1/status/trade/{trade_id}/exit"
        )

    async def get_bot_config(self, bot_name: str) -> Dict[str, Any]:
        """Получение конфигурации бота"""
        return await self._make_request(bot_name, "GET", "/api/v1/config")

    async def update_bot_config(
        self, bot_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обновление конфигурации бота"""
        return await self._make_request(bot_name, "PATCH", "/api/v1/config", config)

    async def get_freqai_prediction(
        self, bot_name: str, pair: str, timeframe: str, strategy: str
    ) -> Dict[str, Any]:
        """Get FreqAI prediction for a pair."""
        return await self._make_request(
            bot_name,
            "GET",
            f"/api/v1/pair_history?pair={pair}&timeframe={timeframe}&strategy={strategy}",
        )

    # === ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ===

    async def get_all_bots_status(self) -> Dict[str, Dict[str, Any]]:
        """Получение статуса всех ботов"""
        results = {}
        for bot_name, connection in self.connections.items():
            status = await self.get_bot_status(bot_name)
            status["ui_url"] = connection.ui_url
            results[bot_name] = status
        return results

    async def start_all_bots(self) -> Dict[str, Dict[str, Any]]:
        """Запуск всех ботов"""
        results = {}
        for bot_name in self.connections.keys():
            results[bot_name] = await self.start_bot(bot_name)
        return results

    async def stop_all_bots(self) -> Dict[str, Dict[str, Any]]:
        """Остановка всех ботов"""
        results = {}
        for bot_name in self.connections.keys():
            results[bot_name] = await self.stop_bot(bot_name)
        return results

    async def health_check_all(self) -> Dict[str, bool]:
        """Проверка здоровья всех подключений"""
        results = {}
        for bot_name, connection in self.connections.items():
            results[bot_name] = (
                connection.is_healthy
                and connection.session
                and not connection.session.closed
            )
        return results

    async def get_connection_stats(self) -> Dict[str, Dict[str, Any]]:
        """Получение статистики подключений"""
        stats = {}
        for bot_name, connection in self.connections.items():
            stats[bot_name] = {
                "url": connection.url,
                "healthy": connection.is_healthy,
                "last_check": connection.last_health_check.isoformat()
                if connection.last_health_check
                else None,
                "retry_count": connection.retry_count,
                "session_active": connection.session is not None
                and not connection.session.closed,
            }
        return stats

    # === МЕТОДЫ ДЛЯ MCP BRIDGE ===

    async def execute_ai_command(
        self, bot_name: str, command: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Выполнение AI команды для бота.
        Используется MCP Bridge для intelligent управления.
        """
        command_map = {
            "start": self.start_bot,
            "stop": self.stop_bot,
            "restart": self.restart_bot,
            "status": self.get_bot_status,
            "profit": self.get_bot_profit,
            "balance": self.get_bot_balance,
            "trades": self.get_open_trades,
            "config": self.get_bot_config,
        }

        if command not in command_map:
            return {"error": f"Unknown command: {command}"}

        try:
            result = await command_map[command](bot_name)

            # Добавление AI контекста
            result.update(
                {
                    "ai_command": command,
                    "bot_name": bot_name,
                    "timestamp": datetime.now().isoformat(),
                    "executed_by": "mcp_bridge",
                }
            )

            return result

        except Exception as e:
            logger.error(f"AI command execution failed: {command} for {bot_name}: {e}")
            return {
                "error": f"Command execution failed: {str(e)}",
                "ai_command": command,
                "bot_name": bot_name,
            }

    async def get_ai_recommendations(self, bot_name: str) -> Dict[str, Any]:
        """
        Получение AI рекомендаций для бота.
        Анализирует статус и предлагает действия.
        """
        status = await self.get_bot_status(bot_name)
        profit = await self.get_bot_profit(bot_name)

        recommendations = []

        # Анализ статуса
        if status.get("state") == "stopped":
            recommendations.append(
                {
                    "action": "start",
                    "reason": "Bot is stopped, consider starting for trading",
                    "confidence": 0.8,
                }
            )

        # Анализ прибыли
        if profit.get("profit_all_coin", 0) < -0.05:  # -5%
            recommendations.append(
                {
                    "action": "stop",
                    "reason": "Significant losses detected, consider stopping",
                    "confidence": 0.9,
                }
            )

        # Анализ открытых сделок
        trades = status.get("trade_count", 0)
        if trades > 10:
            recommendations.append(
                {
                    "action": "reduce_exposure",
                    "reason": "High number of open trades, consider risk management",
                    "confidence": 0.7,
                }
            )

        return {
            "bot_name": bot_name,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self):
        """Корректное завершение работы сервиса"""
        logger.info("Shutting down FtRestClient Service")

        # Закрытие всех сессий
        for connection in self.connections.values():
            if connection.session and not connection.session.closed:
                await connection.session.close()

        self.connections.clear()
        self._initialized = False
        logger.info("FtRestClient Service shutdown complete")


# Глобальный экземпляр сервиса
ft_rest_client_service = FtRestClientService()
