"""
Rate limiting middleware using slowapi.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)

def create_limiter() -> Limiter:
    """
    Create rate limiter instance.

    Returns:
        Configured Limiter instance
    """
    return Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.RATE_LIMIT_REQUESTS} per {settings.RATE_LIMIT_WINDOW} seconds"]
    )

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handle rate limit exceeded errors.

    Args:
        request: FastAPI request
        exc: Rate limit exception

    Returns:
        JSON response with error details
    """
    logger.warning(f"Rate limit exceeded for {request.client.host}: {exc.detail}")

    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "detail": exc.detail,
            "retry_after": exc.retry_after
        },
        headers={"Retry-After": str(exc.retry_after)}
    )
