"""
Request logging middleware.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """
    Middleware for logging HTTP requests and responses.
    """

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info
        method = scope["method"]
        path = scope["path"]
        query = scope.get("query_string", b"").decode()

        # Log request
        start_time = time.time()
        logger.info(f"→ {method} {path}{f'?{query}' if query else ''}")

        # Process request
        await self.app(scope, receive, send)

        # Log response
        process_time = time.time() - start_time
        logger.info(f"← {method} {path} {process_time:.2f}s")
