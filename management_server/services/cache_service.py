"""
Redis-based caching service.
"""

import json
import logging
from typing import Any, Optional, Union
import redis.asyncio as redis

from ..core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis-based caching service with TTL support.
    """

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis: Optional[redis.Redis] = None
        self.prefix = "freqtrade:"

    async def connect(self) -> None:
        """Connect to Redis."""
        if self.redis is None:
            self.redis = redis.from_url(self.redis_url)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            await self.connect()
            value = await self.redis.get(f"{self.prefix}{key}")
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        try:
            await self.connect()
            json_value = json.dumps(value)
            await self.redis.setex(f"{self.prefix}{key}", ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        try:
            await self.connect()
            await self.redis.delete(f"{self.prefix}{key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            await self.connect()
            return bool(await self.redis.exists(f"{self.prefix}{key}"))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in cache.

        Args:
            key: Cache key
            amount: Amount to increment

        Returns:
            New value or None if error
        """
        try:
            await self.connect()
            return await self.redis.incrby(f"{self.prefix}{key}", amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        try:
            await self.connect()
            return bool(await self.redis.expire(f"{self.prefix}{key}", ttl))
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
