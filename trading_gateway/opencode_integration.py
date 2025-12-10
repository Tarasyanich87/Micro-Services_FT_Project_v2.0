from typing import Dict, Any, Optional, AsyncGenerator
import os
import aiohttp
from datetime import datetime
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from fastapi import Depends
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus

class CoreServerClient:
    """HTTP клиент для Core Server API"""

    def __init__(self, session: aiohttp.ClientSession, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self._session = session
        self._auth_token = None

    async def authenticate(self, username: str, password: str):
        """Аутентификация в Core Server"""
        auth_data = {"username": username, "password": password}
        async with self._session.post(f"{self.base_url}/api/auth/login", json=auth_data) as resp:
            if resp.status == 200:
                token_data = await resp.json()
                self._auth_token = token_data.get("access_token")
                return True
        return False

    async def _make_authenticated_request(self, method: str, endpoint: str, **kwargs):
        """HTTP запрос с JWT аутентификацией"""
        headers = {"Authorization": f"Bearer {self._auth_token}"}
        url = f"{self.base_url}{endpoint}"

        async with self._session.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401:
                # Token expired, re-authenticate
                await self.authenticate(
                    os.getenv("CORE_USERNAME", "admin"),
                    os.getenv("CORE_PASSWORD", "admin")
                )
                headers = {"Authorization": f"Bearer {self._auth_token}"}
                async with self._session.request(method, url, headers=headers, **kwargs) as resp:
                    return await resp.json()
            return await resp.json()

async def get_core_server_client() -> AsyncGenerator[CoreServerClient, None]:
    """FastAPI dependency for CoreServerClient."""
    async with aiohttp.ClientSession() as session:
        yield CoreServerClient(session)
=======
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus
>>>>>>> origin/feat/full-microservice-architecture-with-mcp
=======
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus
>>>>>>> origin/feat/project-rebuild-final
=======
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus
>>>>>>> origin/feat/project-rebuild-final-2
=======
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus
>>>>>>> origin/feat/freqai-service-and-fixes
=======
from management_server.tools.redis_streams_event_bus import mcp_streams_event_bus
>>>>>>> origin/feat/frontend-auth-dashboard

class HybridMCPClient:
    """
    Гибридный клиент для взаимодействия с FtRestClient Service.
    Автоматически выбирает оптимальный метод коммуникации.
    """

    def __init__(self, http_client: Optional[CoreServerClient] = None):
        self.http_client = http_client
        self.streams_publisher = MCPCommandPublisher(mcp_streams_event_bus)
        self.direct_service = None
        self._detect_available_methods()

    def _detect_available_methods(self):
        """Определение доступных методов взаимодействия"""
        try:
<<<<<<< HEAD
=======
            # Попытка прямого импорта (для development/single-instance)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> origin/feat/full-microservice-architecture-with-mcp
=======
>>>>>>> origin/feat/project-rebuild-final
=======
>>>>>>> origin/feat/project-rebuild-final-2
=======
>>>>>>> origin/feat/freqai-service-and-fixes
=======
>>>>>>> origin/feat/frontend-auth-dashboard
            from management_server.services.ft_rest_client_service import ft_rest_client_service
            self.direct_service = ft_rest_client_service
            self.preferred_method = "direct"
        except ImportError:
            self.preferred_method = "http" if self.http_client else "none"

    async def initialize(self):
        """Инициализация клиента"""
        if self.http_client:
            await self.http_client.authenticate(
                os.getenv("CORE_USERNAME", "admin"),
                os.getenv("CORE_PASSWORD", "admin")
            )

    # ... (rest of the HybridMCPClient methods are the same)
    async def execute_command(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """
        Интеллектный выбор метода выполнения команды на основе типа операции
        """
        # Критические операции - максимальная надежность
        if action in ["start", "stop", "restart"]:
            return await self._execute_critical_operation(action, bot_name, **kwargs)

        # Аналитические операции - производительность важнее надежности
        elif action in ["status", "metrics", "profit"]:
            return await self._execute_analytics_operation(action, bot_name, **kwargs)

        # AI операции - гибкость и масштабируемость
        elif action in ["analyze", "recommendations", "optimize"]:
            return await self._execute_ai_operation(action, bot_name, **kwargs)

        # Default fallback
        return await self._execute_http_api(action, bot_name, **kwargs)

    async def _execute_critical_operation(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """Критические операции - используем HTTP API для надежности"""
        return await self._execute_http_api(action, bot_name, **kwargs)

    async def _execute_analytics_operation(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """Аналитические операции - используем прямой доступ для производительности"""
        if self.direct_service:
            return await self._execute_direct_service(action, bot_name, **kwargs)
        else:
            return await self._execute_http_api(action, bot_name, **kwargs)

    async def _execute_ai_operation(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """AI операции - используем streams для масштабируемости"""
        return await self._execute_streams(action, bot_name, **kwargs)

    async def _execute_direct_service(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """Прямой вызов FtRestClient Service"""
        try:
            if action == "start":
                result = await self.direct_service.start_bot(bot_name)
            elif action == "stop":
                result = await self.direct_service.stop_bot(bot_name)
            elif action == "status":
                result = await self.direct_service.get_bot_status(bot_name)
            elif action == "metrics":
                result = await self.direct_service.get_bot_profit(bot_name)  # Example
            else:
                return {"error": f"Unsupported action: {action}"}

            result.update({
                "executed_by": "trading_gateway_direct",
                "method": "direct_service",
                "timestamp": datetime.now().isoformat()
            })
            return result

        except Exception as e:
            return {"error": f"Direct service call failed: {str(e)}"}

    async def _execute_http_api(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """HTTP API вызов через Core Server"""
        if not self.http_client:
            return {"error": "HTTP client not available"}

        try:
            endpoint_map = {
                "start": f"/api/freqai/{bot_name}/start",
                "stop": f"/api/freqai/{bot_name}/stop",
                "status": f"/api/bots/{bot_name}/status",
                "metrics": f"/api/freqai/{bot_name}/metrics",
                "profit": f"/api/freqai/{bot_name}/profit"
            }

            if action not in endpoint_map:
                return {"error": f"Unsupported action: {action}"}

            method = "POST" if action in ["start", "stop"] else "GET"
            endpoint = endpoint_map[action]

            result = await self.http_client._make_authenticated_request(method, endpoint, **kwargs)
            result.update({
                "executed_by": "trading_gateway_http",
                "method": "http_api",
                "timestamp": datetime.now().isoformat()
            })
            return result

        except Exception as e:
            return {"error": f"HTTP API call failed: {str(e)}"}

    async def _execute_streams(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """Redis Streams асинхронная коммуникация"""
        try:
            result = await self.streams_publisher.send_bot_command(action, bot_name, **kwargs)
            result.update({
                "executed_by": "trading_gateway_streams",
                "method": "redis_streams",
                "timestamp": datetime.now().isoformat()
            })
            return result

        except Exception as e:
            return {"error": f"Streams communication failed: {str(e)}"}

class MCPCommandPublisher:
    """Publisher для Redis Streams команд"""

    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.pending_responses = {}
        self.response_timeout = 30

    async def send_bot_command(self, action: str, bot_name: str, **kwargs) -> Dict[str, Any]:
        """Отправка команды через Redis Streams"""
        import uuid

        command_id = str(uuid.uuid4())
        command_data = {
            "command_id": command_id,
            "action": action,
            "bot_name": bot_name,
            "parameters": kwargs,
            "source": "trading_gateway",
            "timestamp": datetime.now().isoformat()
        }

        # Публикация команды
        await self.event_bus.publish_system_event("bot_command", command_data)

        # Ожидание ответа (упрощенная версия)
        # В production здесь будет correlation ID handling
        return {"status": "command_sent", "command_id": command_id}

# Dependency for HybridMCPClient
async def get_hybrid_mcp_client(
    core_server_client: CoreServerClient = Depends(get_core_server_client)
) -> HybridMCPClient:
    client = HybridMCPClient(http_client=core_server_client)
    await client.initialize()
    return client
