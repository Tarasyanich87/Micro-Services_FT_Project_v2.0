"""
FreqAI Server client for Management Server
"""

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends

logger = logging.getLogger(__name__)


class FreqAIServerClient:
    """HTTP client for communicating with FreqAI Server"""

    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to FreqAI Server"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"FreqAI Server HTTP error: {e.response.status_code} {e.response.text}"
            )
            return {
                "error": f"HTTP {e.response.status_code}",
                "details": e.response.text,
            }
        except httpx.RequestError as e:
            logger.error(f"FreqAI Server connection error: {e}")
            return {"error": "connection_failed", "details": str(e)}
        except Exception as e:
            logger.exception("Unexpected error in FreqAI Server client")
            return {"error": "unexpected_error", "details": str(e)}

    # --- Device Management ---
    async def get_devices(self) -> Dict[str, Any]:
        """Get device information"""
        return await self._make_request("GET", "/devices")

    # --- Model Management ---
    async def train_model(
        self, model_name: str, model_type: str = "LightGBM"
    ) -> Dict[str, Any]:
        """Train a new model"""
        params = {"model_name": model_name, "model_type": model_type}
        return await self._make_request("POST", "/train-model", params=params)

    async def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """Get model training status"""
        return await self._make_request("GET", f"/models/{model_name}")

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed model information"""
        return await self._make_request("GET", f"/models/{model_name}/info")

    # --- Predictions ---
    async def predict(
        self, model_name: str, features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make prediction using model"""
        return await self._make_request("POST", f"/predict/{model_name}", json=features)

    # --- Health Check ---
    async def health_check(self) -> Dict[str, Any]:
        """Check FreqAI Server health"""
        return await self._make_request("GET", "/health")


# --- FastAPI Dependency ---
_freqai_client: Optional[FreqAIServerClient] = None


def get_freqai_server_client() -> FreqAIServerClient:
    """Get FreqAI Server client instance"""
    global _freqai_client
    if _freqai_client is None:
        _freqai_client = FreqAIServerClient()
    return _freqai_client


async def close_freqai_server_client():
    """Close FreqAI Server client on shutdown"""
    global _freqai_client
    if _freqai_client:
        await _freqai_client.close()
        logger.info("FreqAI Server client closed")
