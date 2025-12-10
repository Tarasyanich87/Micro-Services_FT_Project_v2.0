"""
Asynchronous HTTP client for interacting with the Trading Gateway service.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Optional

import aiohttp
from fastapi import Depends

from ..core.config import settings

logger = logging.getLogger(__name__)


class TradingGatewayClient:
    """
    HTTP client for the Trading Gateway API.
    Manages a persistent aiohttp session for making requests.
    """

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self.base_url = settings.TRADING_GATEWAY_URL

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generic method for making requests to the Trading Gateway."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            async with self._session.request(
                method, url, params=params, json=json_data
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error calling Trading Gateway: {e.status} {e.message}")
            return {"error": "Gateway error", "status": e.status, "detail": e.message}
        except aiohttp.ClientError as e:
            logger.error(f"Connection error to Trading Gateway: {e}")
            return {"error": "Gateway connection failed", "detail": str(e)}
        except Exception as e:
            logger.exception("An unexpected error occurred in TradingGatewayClient")
            return {"error": "An unexpected client error", "detail": str(e)}

    # --- Bot Management ---
    async def start_bot(self, bot_name: str) -> Dict[str, Any]:
        """Send command to start a bot."""
        return await self._make_request("POST", f"/api/v1/bots/{bot_name}/start")

    async def stop_bot(self, bot_name: str) -> Dict[str, Any]:
        """Send command to stop a bot."""
        return await self._make_request("POST", f"/api/v1/bots/{bot_name}/stop")

    async def get_bot_status(self, bot_name: str) -> Dict[str, Any]:
        """Get the status of a specific bot."""
        return await self._make_request("GET", f"/api/v1/bots/{bot_name}/status")

    async def get_all_bots_status(self) -> Dict[str, Any]:
        """Get the status of all bots known to the gateway."""
        return await self._make_request("GET", "/api/v1/bots/status")

    # --- FreqAI Operations ---
    async def get_pair_history(
        self, bot_name: str, pair: str, timeframe: str, strategy: str, timerange: str
    ) -> Dict[str, Any]:
        """Request historical data for a pair, analyzed by a strategy (for FreqAI)."""
        params = {
            "pair": pair,
            "timeframe": timeframe,
            "strategy": strategy,
            "timerange": timerange,
        }
        return await self._make_request(
            "GET", f"/api/v1/bots/{bot_name}/pair_history", params=params
        )


# --- FastAPI Dependency ---

_trading_gateway_client_session: Optional[aiohttp.ClientSession] = None

async def get_trading_gateway_client() -> AsyncGenerator[TradingGatewayClient, None]:
    """
    FastAPI dependency that provides a TradingGatewayClient with a managed session.
    """
    global _trading_gateway_client_session
    if _trading_gateway_client_session is None or _trading_gateway_client_session.closed:
        _trading_gateway_client_session = aiohttp.ClientSession()

    yield TradingGatewayClient(_trading_gateway_client_session)
    # The session is closed on application shutdown

async def close_trading_gateway_client():
    """Function to close the session on application shutdown."""
    global _trading_gateway_client_session
    if _trading_gateway_client_session and not _trading_gateway_client_session.closed:
        await _trading_gateway_client_session.close()
        logger.info("Trading Gateway client session closed.")

# In your application's lifespan manager, you would call close_trading_gateway_client.
# This setup avoids creating a new session for every request.
