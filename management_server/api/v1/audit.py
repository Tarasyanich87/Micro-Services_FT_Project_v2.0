from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from management_server.database import get_db
from management_server.services.audit_service import AuditService
from management_server.auth.dependencies import get_current_active_user
from management_server.models.models import User
import datetime

class AuditLogResponse(BaseModel):
    id: int
    created_at: datetime.datetime
    username: str | None
    ip_address: str | None
    http_method: str
    path: str
    status_code: int

    class Config:
        orm_mode = True

router = APIRouter()

def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: AuditService = Depends(get_audit_service),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the latest audit logs with pagination.
    """
    logs = await service.get_logs(limit=limit, offset=skip)
    return logs
