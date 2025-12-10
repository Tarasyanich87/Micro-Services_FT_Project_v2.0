import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from management_server.models.models import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    """Service for logging audit trails."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def log(
        self,
        action: str,
        status_code: int,
        http_method: str,
        path: str,
        ip_address: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Creates a new audit log entry."""
        try:
            log_entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                details=details,
                status_code=status_code,
                http_method=http_method,
                path=path,
                ip_address=ip_address
            )
            self.db_session.add(log_entry)
            await self.db_session.commit()
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            await self.db_session.rollback()

    async def get_logs(self, limit: int = 100, offset: int = 0):
        """Retrieves audit logs."""
        result = await self.db_session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()
