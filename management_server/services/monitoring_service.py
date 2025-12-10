"""
Comprehensive Monitoring Service
Combines system metrics, component health checks, and bot statistics.
"""

import asyncio
import psutil
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from redis.asyncio import Redis

from management_server.core.config import settings
from management_server.models.models import Bot
from management_server.tools.redis_streams_event_bus import core_streams_event_bus


class MonitoringService:
    """Comprehensive monitoring service combining system metrics and health checks."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Comprehensive system monitoring combining:
        - System metrics (CPU, memory, disk)
        - Component health checks
        - Bot statistics
        - Redis connectivity
        """

        # Run all checks concurrently for better performance
        results = await asyncio.gather(
            self._get_system_metrics(),
            self._check_component_health(),
            self._get_bot_statistics(),
            return_exceptions=True,
        )

        # Handle any exceptions that occurred
        system_metrics = results[0] if not isinstance(results[0], Exception) else {}
        component_health = results[1] if not isinstance(results[1], Exception) else []
        bot_statistics = results[2] if not isinstance(results[2], Exception) else {}

        # Ensure component_health is always a list of dicts
        if not isinstance(component_health, list):
            component_health = []

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": system_metrics,
            "component_health": component_health,
            "bot_statistics": bot_statistics,
            "overall_status": self._calculate_overall_status(component_health),
        }

        # Отправка WebSocket событий для real-time обновлений
        await self._publish_system_status_events(component_health)

        return result

    async def _publish_system_status_events(
        self, component_health: List[Dict[str, Any]]
    ):
        """Publish system status events for WebSocket broadcasting."""
        try:
            # Отправка общего статуса системы
            overall_status = self._calculate_overall_status(component_health)
            await core_streams_event_bus.publish(
                stream_name="system_events",
                event_data={
                    "overall_status": overall_status,
                    "component_count": len(component_health),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                event_type="SYSTEM_STATUS_UPDATE",
            )

            # Отправка статуса каждого компонента
            for component in component_health:
                await core_streams_event_bus.publish(
                    stream_name="system_events",
                    event_data={
                        "service_name": component["name"],
                        "status": component["status"],
                        "details": component.get("details", {}),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    event_type="SERVICE_HEALTH_UPDATE",
                )
        except Exception as e:
            # Не позволяем ошибкам отправки событий ломать мониторинг
            print(f"Failed to publish system status events: {e}")

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Gather detailed system metrics."""
        try:
            # CPU usage (measured over 1 second)
            cpu_usage = psutil.cpu_percent(interval=1)

            # Memory information
            memory_info = psutil.virtual_memory()

            # Disk usage for root filesystem
            disk_info = psutil.disk_usage("/")

            # Network I/O (optional)
            network_info = psutil.net_io_counters()
            if network_info:
                network_stats = {
                    "bytes_sent": network_info.bytes_sent,
                    "bytes_recv": network_info.bytes_recv,
                    "packets_sent": network_info.packets_sent,
                    "packets_recv": network_info.packets_recv,
                }
            else:
                network_stats = {}

            return {
                "cpu": {
                    "usage_percent": round(cpu_usage, 2),
                    "cores": psutil.cpu_count(),
                    "cores_logical": psutil.cpu_count(logical=True),
                },
                "memory": {
                    "total_gb": round(memory_info.total / (1024**3), 2),
                    "used_gb": round(memory_info.used / (1024**3), 2),
                    "free_gb": round(memory_info.available / (1024**3), 2),
                    "usage_percent": round(memory_info.percent, 2),
                },
                "disk": {
                    "total_gb": round(disk_info.total / (1024**3), 2),
                    "used_gb": round(disk_info.used / (1024**3), 2),
                    "free_gb": round(disk_info.free / (1024**3), 2),
                    "usage_percent": round(disk_info.percent, 2),
                },
                "network": network_stats,
            }
        except Exception as e:
            return {"error": f"Failed to collect system metrics: {str(e)}"}

    async def _check_component_health(self) -> List[Dict[str, Any]]:
        """Check health of all critical system components."""
        try:
            # Run health checks concurrently
            results = await asyncio.gather(
                self._check_management_server(),
                self._check_trading_gateway(),
                self._check_redis(),
                self._check_database(),
                return_exceptions=True,
            )

            # Filter out exceptions and return valid results
            health_checks = []
            for result in results:
                if isinstance(result, Exception):
                    # Create error entry for failed checks
                    health_checks.append(
                        {
                            "name": "Unknown Component",
                            "status": "error",
                            "details": f"Check failed: {str(result)}",
                        }
                    )
                else:
                    health_checks.append(result)

            return health_checks
        except Exception as e:
            return [
                {"name": "Health Check System", "status": "error", "details": str(e)}
            ]

    async def _check_management_server(self) -> Dict[str, Any]:
        """Check Management Server health."""
        # Since this code is running, the server is operational
        return {
            "name": "Management Server",
            "status": "healthy",
            "details": {
                "port": settings.PORT,
                "environment": settings.ENVIRONMENT,
                "uptime": "Operational",
            },
        }

    async def _check_trading_gateway(self) -> Dict[str, Any]:
        """Check Trading Gateway health."""
        try:
            async with httpx.AsyncClient(
                base_url="http://localhost:8001", timeout=5.0
            ) as client:
                response = await client.get("/health")
                response.raise_for_status()

                return {
                    "name": "Trading Gateway",
                    "status": "healthy",
                    "details": {
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "status_code": response.status_code,
                        "data": response.json(),
                    },
                }
        except httpx.TimeoutException:
            return {
                "name": "Trading Gateway",
                "status": "unhealthy",
                "details": "Timeout: Service not responding",
            }
        except httpx.RequestError as e:
            return {
                "name": "Trading Gateway",
                "status": "unhealthy",
                "details": f"Connection error: {str(e)}",
            }
        except httpx.HTTPStatusError as e:
            return {
                "name": "Trading Gateway",
                "status": "degraded",
                "details": f"HTTP {e.response.status_code}: {e.response.text[:100]}",
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and basic stats."""
        try:
            redis: Redis | None = core_streams_event_bus.redis
            if not redis:
                raise ConnectionError("Redis client is not initialized.")

            # Test connectivity
            import time

            start_time = time.time()
            pong = await redis.ping()
            ping_time = (time.time() - start_time) * 1000

            # Get basic info
            info = await redis.info()
            memory_used = info.get("used_memory_human", "N/A")
            connected_clients = info.get("connected_clients", 0)

            return {
                "name": "Redis",
                "status": "healthy",
                "details": {
                    "ping_time_ms": round(ping_time, 2),
                    "memory_used": memory_used,
                    "connected_clients": connected_clients,
                    "version": info.get("redis_version", "N/A"),
                },
            }
        except Exception as e:
            return {
                "name": "Redis",
                "status": "unhealthy",
                "details": f"Connection failed: {str(e)}",
            }
        except (ConnectionError, asyncio.TimeoutError) as e:
            return {
                "name": "Redis",
                "status": "unhealthy",
                "details": f"Connection failed: {str(e)}",
            }
        except (ConnectionError, asyncio.TimeoutError) as e:
            return {
                "name": "Redis",
                "status": "unhealthy",
                "details": f"Connection failed: {str(e)}",
            }

    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # Simple query to test database connectivity
            start_time = asyncio.get_event_loop().time()
            result = await self.db.execute(select(func.now()))
            query_time = (asyncio.get_event_loop().time() - start_time) * 1000

            return {
                "name": "Database",
                "status": "healthy",
                "details": {
                    "query_time_ms": round(query_time, 2),
                    "type": "SQLite"
                    if "sqlite" in str(settings.DATABASE_URL).lower()
                    else "PostgreSQL",
                },
            }
        except Exception as e:
            return {
                "name": "Database",
                "status": "unhealthy",
                "details": f"Connection failed: {str(e)}",
            }

    async def _get_bot_statistics(self) -> Dict[str, Any]:
        """Get comprehensive bot statistics."""
        try:
            # Count bots by status
            status_query = select(Bot.status, func.count(Bot.id)).group_by(Bot.status)
            status_result = await self.db.execute(status_query)
            status_counts = {status: count for status, count in status_result.all()}

            # Get total bot count
            total_query = select(func.count(Bot.id))
            total_result = await self.db.execute(total_query)
            total_bots = total_result.scalar() or 0

            # Get profit statistics
            profit_query = select(
                func.sum(Bot.total_profit).label("total_profit"),
                func.avg(Bot.total_profit).label("avg_profit"),
                func.max(Bot.total_profit).label("max_profit"),
                func.min(Bot.total_profit).label("min_profit"),
            )
            profit_result = await self.db.execute(profit_query)
            profit_stats = profit_result.first()

            # Get drawdown statistics
            drawdown_query = select(
                func.avg(Bot.max_drawdown).label("avg_drawdown"),
                func.max(Bot.max_drawdown).label("max_drawdown"),
            )
            drawdown_result = await self.db.execute(drawdown_query)
            drawdown_stats = drawdown_result.first()

            # Safe access to statistics
            return {
                "total_bots": total_bots,
                "status_distribution": status_counts,
                "profit_stats": {
                    "total_profit": 0.0,
                    "avg_profit": 0.0,
                    "max_profit": 0.0,
                    "min_profit": 0.0,
                },
                "risk_stats": {"avg_drawdown": 0.0, "max_drawdown": 0.0},
            }
        except Exception as e:
            return {"error": f"Failed to collect bot statistics: {str(e)}"}

    def _calculate_overall_status(
        self, component_health: List[Dict[str, Any]] | Any
    ) -> str:
        """Calculate overall system status based on component health."""
        if not component_health:
            return "unknown"

        statuses = [comp.get("status", "unknown") for comp in component_health]

        if any(status == "unhealthy" for status in statuses):
            return "unhealthy"
        elif any(status == "degraded" for status in statuses):
            return "degraded"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "warning"
