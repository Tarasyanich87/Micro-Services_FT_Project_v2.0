"""
FreqAI Model Handler for Trading Gateway
Provides LRU caching and lifecycle management for FreqAI models
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import base64

logger = logging.getLogger(__name__)


class FreqAIModelHandler:
    """
    Handles FreqAI model storage, caching, and lifecycle management.
    Uses LRU (Least Recently Used) cache to manage memory efficiently.
    """

    def __init__(
        self,
        cache_dir: str = "/tmp/freqai_cache",
        max_cache_size: int = 5,
        max_model_size_mb: int = 50,
    ):
        """
        Initialize the model handler.

        Args:
            cache_dir: Directory for temporary model storage
            max_cache_size: Maximum number of models to cache
            max_model_size_mb: Maximum model file size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.max_cache_size = max_cache_size
        self.max_model_size_bytes = max_model_size_mb * 1024 * 1024

        # LRU cache: bot_name -> model_path
        self.cache: Dict[str, str] = {}
        self.access_times: Dict[str, float] = {}

        logger.info(
            f"FreqAIModelHandler initialized: cache_dir={cache_dir}, max_size={max_cache_size}"
        )

    async def store_model_for_bot(
        self, bot_name: str, model_data: Dict[str, str]
    ) -> str:
        """
        Decode base64 model data and store it for a specific bot.
        Uses LRU cache management.

        Args:
            bot_name: Name of the bot
            model_data: Dict with 'filename' and 'content_b64' keys

        Returns:
            Path to the stored model file

        Raises:
            ValueError: If model data is invalid or too large
            OSError: If file operations fail
        """
        if not bot_name or not isinstance(bot_name, str):
            raise ValueError("Invalid bot_name provided")

        if not model_data or not isinstance(model_data, dict):
            raise ValueError("Invalid model_data provided")

        try:
            filename = model_data.get("filename")
            content_b64 = model_data.get("content_b64")

            if not filename or not content_b64:
                raise ValueError("Missing filename or content_b64 in model data")

            # Validate filename (basic security)
            if not filename.endswith(".joblib"):
                raise ValueError("Only .joblib files are supported")

            # Validate filename doesn't contain path traversal
            if ".." in filename or "/" in filename or "\\" in filename:
                raise ValueError("Invalid filename: path traversal not allowed")

            # Decode base64
            try:
                model_content = base64.b64decode(content_b64)
            except Exception as e:
                raise ValueError(f"Invalid base64 content: {e}")

            # Check size
            if len(model_content) > self.max_model_size_bytes:
                raise ValueError(
                    f"Model too large: {len(model_content)} bytes (max: {self.max_model_size_bytes})"
                )

            # Generate unique filename to avoid conflicts
            unique_filename = f"{bot_name}_{int(time.time())}_{filename}"
            model_path = self.cache_dir / unique_filename

            # Ensure cache directory exists
            self.cache_dir.mkdir(exist_ok=True)

            # Write model file atomically
            temp_path = model_path.with_suffix(".tmp")
            try:
                with open(temp_path, "wb") as f:
                    f.write(model_content)
                temp_path.rename(model_path)  # Atomic move
            except OSError as e:
                if temp_path.exists():
                    temp_path.unlink()  # Cleanup temp file
                raise OSError(f"Failed to write model file: {e}")

            # Update LRU cache
            self._update_cache(bot_name, str(model_path))

            logger.info(f"FreqAI model stored for bot {bot_name}: {model_path}")
            return str(model_path)

        except (ValueError, OSError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error storing FreqAI model for bot {bot_name}: {e}"
            )
            raise RuntimeError(f"Failed to store FreqAI model: {e}")

    def get_model_path(self, bot_name: str) -> Optional[str]:
        """
        Get the cached model path for a bot.
        Updates LRU access time.

        Args:
            bot_name: Name of the bot

        Returns:
            Path to model file or None if not cached
        """
        if bot_name in self.cache:
            self.access_times[bot_name] = time.time()
            return self.cache[bot_name]
        return None

    async def cleanup_bot_models(self, bot_name: str):
        """
        Remove all cached models for a specific bot.
        Called when bot is stopped.

        Args:
            bot_name: Name of the bot

        Raises:
            ValueError: If bot_name is invalid
        """
        if not bot_name or not isinstance(bot_name, str):
            raise ValueError("Invalid bot_name provided")

        if bot_name in self.cache:
            model_path = self.cache[bot_name]

            # Remove file if it exists
            if os.path.exists(model_path):
                try:
                    os.remove(model_path)
                    logger.info(
                        f"Removed FreqAI model file for bot {bot_name}: {model_path}"
                    )
                except OSError as e:
                    logger.warning(f"Failed to remove model file {model_path}: {e}")
                    # Continue cleanup even if file removal fails
                except Exception as e:
                    logger.error(
                        f"Unexpected error removing model file {model_path}: {e}"
                    )

            # Remove from cache
            del self.cache[bot_name]
            del self.access_times[bot_name]

            logger.debug(f"Cleaned up FreqAI cache for bot {bot_name}")
        else:
            logger.debug(f"No cached models found for bot {bot_name}")

    def _update_cache(self, bot_name: str, model_path: str):
        """
        Update LRU cache with new model.
        Evicts least recently used items if cache is full.

        Args:
            bot_name: Name of the bot
            model_path: Path to the model file
        """
        # If bot already in cache, just update access time
        if bot_name in self.cache:
            self.access_times[bot_name] = time.time()
            return

        # Check if cache is full
        if len(self.cache) >= self.max_cache_size:
            # Find least recently used
            lru_bot = min(self.access_times.keys(), key=lambda k: self.access_times[k])

            # Remove LRU item
            lru_path = self.cache[lru_bot]
            if os.path.exists(lru_path):
                try:
                    os.remove(lru_path)
                    logger.info(f"Evicted LRU model for bot {lru_bot}: {lru_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove evicted model {lru_path}: {e}")

            del self.cache[lru_bot]
            del self.access_times[lru_bot]

        # Add new item
        self.cache[bot_name] = model_path
        self.access_times[bot_name] = time.time()

        logger.debug(f"Cache updated: {len(self.cache)}/{self.max_cache_size} models")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with cache statistics
        """
        return {
            "cached_models": len(self.cache),
            "max_cache_size": self.max_cache_size,
            "cache_hit_rate": self._calculate_hit_rate(),
            "oldest_access": min(self.access_times.values())
            if self.access_times
            else None,
            "newest_access": max(self.access_times.values())
            if self.access_times
            else None,
        }

    def _calculate_hit_rate(self) -> float:
        """
        Calculate cache hit rate (simplified version).
        In production, you'd track hits/misses over time.

        Returns:
            Hit rate as percentage
        """
        # Simplified: assume all current cache entries are hits
        total_entries = len(self.cache)
        return 100.0 if total_entries > 0 else 0.0

    async def cleanup_all(self):
        """
        Clean up all cached models and files.
        Called during shutdown.
        """
        logger.info("Cleaning up all FreqAI model cache")

        for bot_name, model_path in self.cache.items():
            if os.path.exists(model_path):
                try:
                    os.remove(model_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {model_path}: {e}")

        self.cache.clear()
        self.access_times.clear()

        logger.info("FreqAI model cache cleanup complete")


# Global instance
freqai_model_handler = FreqAIModelHandler()
