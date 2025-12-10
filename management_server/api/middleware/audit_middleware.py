from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from management_server.database import SessionLocal
from management_server.services.audit_service import AuditService
from management_server.core.config import settings


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # We don't want to log OPTIONS requests as they are pre-flight checks
        if request.method == "OPTIONS":
            return response

        user_id: int | None = None
        username: str | None = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
                )
                user_id = payload.get("sub")
                username = payload.get("username")
            except jwt.PyJWTError:
                # Invalid token, but we still log the attempt
                pass

        async with SessionLocal() as db_session:
            audit_service = AuditService(db_session=db_session)
            await audit_service.log(
                action=f"API Request: {request.method} {request.url.path}",
                status_code=response.status_code,
                http_method=request.method,
                path=request.url.path,
                ip_address=request.client.host if request.client else "unknown",
                user_id=user_id,
                username=username,
            )

        return response
