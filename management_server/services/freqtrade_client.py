"""
A client for interacting with the Freqtrade bot's REST API.
"""
import logging
from typing import Any, Dict, Optional

import aiohttp
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class FreqtradeClient:
    def __init__(self, bot_url: str, username: str, password: str):
        # The bot_url should be the base URL, e.g., http://localhost:8081
        self.base_url = bot_url.rstrip('/')
        self.username = username
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None
        self._jwt_token: Optional[str] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _login(self):
        """Logs into the Freqtrade API and stores the JWT token."""
        session = await self._get_session()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/token/login",
                auth=aiohttp.BasicAuth(self.username, self.password)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                self._jwt_token = data.get("access_token")
                logger.info(f"Successfully logged into Freqtrade API at {self.base_url}")
        except aiohttp.ClientError as e:
            logger.error(f"Failed to log into Freqtrade API at {self.base_url}: {e}")
            self._jwt_token = None

    async def _get_headers(self) -> Dict[str, str]:
        if not self._jwt_token:
            await self._login()

        if not self._jwt_token:
             raise HTTPException(status_code=503, detail="Could not authenticate with Freqtrade bot API.")

        return {"Authorization": f"Bearer {self._jwt_token}"}

    async def get_pair_history(self, pair: str, timeframe: str, strategy: str) -> Dict[str, Any]:
        """
        Fetches the analyzed pair history from the bot, which includes FreqAI predictions.
        We'll ask for only the last 2 candles to be safe.
        """
        session = await self._get_session()
        headers = await self._get_headers()
        params = {
            "pair": pair,
            "timeframe": timeframe,
            "strategy": strategy,
            "limit": 2
        }
        try:
            async with session.get(f"{self.base_url}/api/v1/pair_history", headers=headers, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching pair history from {self.base_url}: {e}")
            # If token is expired, it might be a 401, try to login again on next call.
            if response.status == 401:
                self._jwt_token = None
            raise HTTPException(status_code=503, detail=f"Failed to fetch data from Freqtrade bot: {e}")
