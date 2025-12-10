"""
Custom error handling for the API.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class APIError(Exception):
    """
    Custom API error with structured error information.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle APIError exceptions.

    Args:
        request: FastAPI request
        exc: APIError exception

    Returns:
        JSON response with error details
    """
    logger.error(
        f"API Error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

def create_validation_error(field: str, message: str) -> APIError:
    """Create validation error."""
    return APIError(
        message=f"Validation error for field '{field}': {message}",
        error_code="VALIDATION_ERROR",
        status_code=422,
        details={"field": field, "validation_message": message}
    )

def create_not_found_error(resource: str, resource_id: str = None) -> APIError:
    """Create not found error."""
    message = f"{resource} not found"
    if resource_id:
        message += f": {resource_id}"

    return APIError(
        message=message,
        error_code="NOT_FOUND",
        status_code=404,
        details={"resource": resource, "resource_id": resource_id}
    )

def create_permission_error(action: str, resource: str = None) -> APIError:
    """Create permission error."""
    message = f"Insufficient permissions to {action}"
    if resource:
        message += f" {resource}"

    return APIError(
        message=message,
        error_code="PERMISSION_DENIED",
        status_code=403,
        details={"action": action, "resource": resource}
    )
