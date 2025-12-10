"""
Unit tests for Audit Service.
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from management_server.services.audit_service import AuditService
from management_server.models.models import AuditLog


class TestAuditService:
    """Test cases for AuditService."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def audit_service(self, mock_db_session):
        """Create AuditService instance with mocked session."""
        return AuditService(db_session=mock_db_session)

    @pytest.mark.asyncio
    async def test_log_success(self, audit_service, mock_db_session):
        """Test successful audit log creation."""
        await audit_service.log(
            action="POST /api/v1/bots/123/start",
            status_code=200,
            http_method="POST",
            path="/api/v1/bots/123/start",
            ip_address="192.168.1.100",
            user_id=123,
            username="testuser",
            details={"processing_time_ms": 150.5, "user_agent": "Mozilla/5.0"},
        )

        # Verify that add and commit were called
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # Verify the audit log object
        call_args = mock_db_session.add.call_args[0][0]
        assert isinstance(call_args, AuditLog)
        assert call_args.action == "POST /api/v1/bots/123/start"
        assert call_args.status_code == 200
        assert call_args.http_method == "POST"
        assert call_args.path == "/api/v1/bots/123/start"
        assert call_args.ip_address == "192.168.1.100"
        assert call_args.user_id == 123
        assert call_args.username == "testuser"
        assert call_args.details == {
            "processing_time_ms": 150.5,
            "user_agent": "Mozilla/5.0",
        }

    @pytest.mark.asyncio
    async def test_log_minimal_data(self, audit_service, mock_db_session):
        """Test audit log creation with minimal required data."""
        await audit_service.log(
            action="GET /api/v1/bots",
            status_code=200,
            http_method="GET",
            path="/api/v1/bots",
            ip_address="127.0.0.1",
        )

        call_args = mock_db_session.add.call_args[0][0]
        assert call_args.user_id is None
        assert call_args.username is None
        assert call_args.details is None

    @pytest.mark.asyncio
    async def test_log_database_error(self, audit_service, mock_db_session):
        """Test audit log creation with database error."""
        mock_db_session.commit.side_effect = Exception("Database connection failed")

        # Should not raise exception, just log the error
        await audit_service.log(
            action="POST /api/v1/bots",
            status_code=500,
            http_method="POST",
            path="/api/v1/bots",
            ip_address="127.0.0.1",
        )

        # Should still try to add and commit
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logs_default_params(self, audit_service, mock_db_session):
        """Test getting audit logs with default parameters."""
        mock_scalars = AsyncMock()
        mock_logs = [AsyncMock(), AsyncMock(), AsyncMock()]
        mock_scalars.all.return_value = mock_logs
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db_session.execute.return_value = mock_result

        result = await audit_service.get_logs()

        assert result == mock_logs
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logs_with_pagination(self, audit_service, mock_db_session):
        """Test getting audit logs with pagination."""
        mock_scalars = AsyncMock()
        mock_logs = [AsyncMock(), AsyncMock()]
        mock_scalars.all.return_value = mock_logs
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db_session.execute.return_value = mock_result

        result = await audit_service.get_logs(limit=50, offset=100)

        assert result == mock_logs
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logs_empty_result(self, audit_service, mock_db_session):
        """Test getting audit logs when no logs exist."""
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = []
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db_session.execute.return_value = mock_result

        result = await audit_service.get_logs(limit=10)

        assert result == []
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logs_with_pagination(self, audit_service, mock_db_session):
        """Test getting audit logs with pagination."""
        mock_result = AsyncMock()
        mock_logs = [AsyncMock(), AsyncMock()]
        mock_result.scalars.return_value.all.return_value = mock_logs

        mock_db_session.execute.return_value = mock_result

        result = await audit_service.get_logs(limit=50, offset=100)

        assert result == mock_logs
        # Verify the query was constructed with correct limit and offset
        call_args = mock_db_session.execute.call_args[0][0]
        # The select query should have limit(50).offset(100)

    @pytest.mark.asyncio
    async def test_get_logs_empty_result(self, audit_service, mock_db_session):
        """Test getting audit logs when no logs exist."""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db_session.execute.return_value = mock_result

        result = await audit_service.get_logs(limit=10)

        assert result == []
