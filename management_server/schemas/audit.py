from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class AuditLogResponse(BaseModel):
    id: int
    created_at: datetime
    username: Optional[str] = None
    ip_address: Optional[str] = None
    http_method: str
    path: str
    status_code: int
    action: str

    class Config:
        from_attributes = True

class PaginatedAuditLogsResponse(BaseModel):
    total: int
    logs: List[AuditLogResponse]
