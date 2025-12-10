import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
import jwt

from management_server.database import SessionLocal
from management_server.services.audit_service import AuditService
from management_server.auth.jwt import ALGORITHM, SECRET_KEY

class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        if request.method == "OPTIONS" or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json"):
            return response

        user_id: int | None = None
        username: str | None = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username = payload.get("sub")
            except jwt.PyJWTError:
                username = "invalid_token"

        action = f"{request.method} {request.url.path}"

        details = {
            "processing_time_ms": round(process_time * 1000, 2),
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        async with SessionLocal() as db:
            audit_service = AuditService(db)
            await audit_service.log(
                action=action,
                details=details,
                username=username,
                user_id=user_id,
                status_code=response.status_code,
                http_method=request.method,
                path=request.url.path,
                ip_address=request.client.host if request.client else "unknown",
            )

        return response
