import pytest
from unittest.mock import AsyncMock, patch
from management_server.services.bot_service import BotService
from management_server.models.models import BotCreate, BotUpdate, BotStatus


@pytest.fixture
def bot_service():
    """Provides a BotService instance with mocked dependencies."""
    # Mock dependencies
    mock_repo = AsyncMock()
    mock_model_repo = AsyncMock()
    mock_tg_client = AsyncMock()
    mock_event_bus = AsyncMock()

    service = BotService(
        bot_repo=mock_repo,
        model_repo=mock_model_repo,
        tg_client=mock_tg_client,
        event_bus=mock_event_bus,
    )

    return service, mock_repo, mock_model_repo, mock_tg_client, mock_event_bus


class TestBotService:
    """Test cases for BotService."""

    @pytest.mark.asyncio
    async def test_get_all_bots_success(self, bot_service):
        """Test successful retrieval of all bots."""
        service, mock_repo, _, _, _ = bot_service

        # Mock user and expected result
        mock_user = AsyncMock()
        mock_user.id = 1
        expected_bots = [AsyncMock(), AsyncMock()]

        mock_repo.get_all.return_value = expected_bots

        # Execute
        result = await service.get_all_bots(mock_user, skip=0, limit=10)

        # Assert
        assert result == expected_bots
        mock_repo.get_all.assert_called_once_with(1, 0, 10)

    @pytest.mark.asyncio
    async def test_create_bot_success(self, bot_service):
        """Test successful bot creation."""
        service, mock_repo, _, _, _ = bot_service

        # Mock data
        mock_user = AsyncMock()
        mock_user.id = 1
        bot_data = BotCreate(
            name="test_bot",
            strategy_name="TestStrategy",
            exchange="binance",
            stake_currency="USDT",
            stake_amount=100.0,
        )
        expected_bot = AsyncMock()

        mock_repo.create.return_value = expected_bot

        # Execute
        result = await service.create_bot(bot_data, mock_user)

        # Assert
        assert result == expected_bot
        mock_repo.create.assert_called_once()
        call_args = mock_repo.create.call_args[0]
        assert call_args[0] == bot_data
        assert call_args[1] == 1

    @pytest.mark.asyncio
    async def test_create_bot_generates_config(self, bot_service):
        """Test that create_bot generates full Freqtrade config."""
        service, mock_repo, _, _, _ = bot_service

        # Mock data
        mock_user = AsyncMock()
        mock_user.id = 1
        bot_data = BotCreate(
            name="test_bot",
            strategy_name="TestStrategy",
            exchange="binance",
            stake_currency="USDT",
            stake_amount=100.0,
        )
        expected_bot = AsyncMock()

        mock_repo.create.return_value = expected_bot

        # Execute
        await service.create_bot(bot_data, mock_user)

        # Assert config was generated
        call_args = mock_repo.create.call_args[0]
        created_bot_data = call_args[0]
        assert hasattr(created_bot_data, "config")
        config = created_bot_data.config

        # Check required config fields
        assert config["trading_mode"] == "spot"
        assert config["dry_run"] is True
        assert config["exchange"]["name"] == "binance"
        assert config["strategy"] == "TestStrategy"

    @pytest.mark.asyncio
    async def test_get_bot_by_id_success(self, bot_service):
        """Test successful retrieval of bot by ID."""
        service, mock_repo, _, _, _ = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        expected_bot = AsyncMock()
        bot_id = 123

        mock_repo.get_by_id.return_value = expected_bot

        # Execute
        result = await service.get_bot_by_id(bot_id, mock_user)

        # Assert
        assert result == expected_bot
        mock_repo.get_by_id.assert_called_once_with(bot_id, 1)

    @pytest.mark.asyncio
    async def test_get_bot_by_id_not_found(self, bot_service):
        """Test bot retrieval when bot doesn't exist."""
        service, mock_repo, _, _, _ = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        bot_id = 123

        mock_repo.get_by_id.return_value = None

        # Execute
        result = await service.get_bot_by_id(bot_id, mock_user)

        # Assert
        assert result is None
        mock_repo.get_by_id.assert_called_once_with(bot_id, 1)

    @pytest.mark.asyncio
    async def test_update_bot_success(self, bot_service):
        """Test successful bot update."""
        service, mock_repo, _, _, _ = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        bot_id = 123

        # Mock existing bot
        mock_bot = AsyncMock()
        mock_bot.status = "stopped"
        mock_repo.get_by_id.return_value = mock_bot

        # Mock updated bot
        updated_bot = AsyncMock()
        mock_repo.update.return_value = updated_bot

        # Update data
        update_data = BotUpdate(name="new_name")

        # Execute
        result = await service.update_bot(bot_id, update_data, mock_user)

        # Assert
        assert result == updated_bot
        mock_repo.update.assert_called_once_with(bot_id, update_data, 1)

    @pytest.mark.asyncio
    async def test_update_bot_running_sets_restart_required(self, bot_service):
        """Test that updating a running bot sets restart_required flag."""
        service, mock_repo, _, _, _ = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        bot_id = 123

        # Mock running bot
        mock_bot = AsyncMock()
        mock_bot.status = "running"
        mock_repo.get_by_id.return_value = mock_bot

        # Mock updated bot
        updated_bot = AsyncMock()
        mock_repo.update.return_value = updated_bot

        # Update data
        update_data = BotUpdate(name="new_name")

        # Execute
        result = await service.update_bot(bot_id, update_data, mock_user)

        # Assert restart_required was set
        assert update_data.restart_required is True
        mock_repo.update.assert_called_once_with(bot_id, update_data, 1)

    @pytest.mark.asyncio
    async def test_update_bot_not_found(self, bot_service):
        """Test bot update when bot doesn't exist."""
        service, mock_repo, _, _, _ = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        bot_id = 123

        mock_repo.get_by_id.return_value = None
        update_data = BotUpdate(name="new_name")

        # Execute
        result = await service.update_bot(bot_id, update_data, mock_user)

        # Assert
        assert result is None
        mock_repo.get_by_id.assert_called_once_with(bot_id, 1)
        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_bot_success(self, bot_service):
        """Test successful bot deletion."""
        service, mock_repo, _, _, _ = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        bot_id = 123

        mock_repo.delete.return_value = True

        # Execute
        result = await service.delete_bot(bot_id, mock_user)

        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(bot_id, 1)

    @pytest.mark.asyncio
    async def test_start_bot_success(self, bot_service):
        """Test successful bot start."""
        service, mock_repo, _, mock_tg_client, mock_event_bus = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        bot_id = 123

        # Mock bot
        mock_bot = AsyncMock()
        mock_bot.id = bot_id
        mock_bot.name = "test_bot"
        mock_bot.config = {}
        mock_repo.get_by_id.return_value = mock_bot

        # Execute
        result = await service.start_bot(bot_id, mock_user)

        # Assert
        assert "status" in result
        assert "bot_name" in result
        mock_repo.get_by_id.assert_called_once_with(bot_id, 1)
        mock_repo.update_bot_status.assert_called_once_with(bot_id, BotStatus.STARTING)
        assert (
            mock_event_bus.publish.call_count == 2
        )  # One for mcp_commands, one for bot_events

    @pytest.mark.asyncio
    async def test_start_bot_not_found(self, bot_service):
        """Test bot start when bot doesn't exist."""
        service, mock_repo, _, _, _ = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        bot_id = 123

        mock_repo.get_by_id.return_value = None

        # Execute
        result = await service.start_bot(bot_id, mock_user)

        # Assert
        assert "error" in result
        mock_repo.get_by_id.assert_called_once_with(bot_id, 1)
        mock_repo.update_bot_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_bot_success(self, bot_service):
        """Test successful bot stop."""
        service, mock_repo, _, mock_tg_client, mock_event_bus = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        bot_id = 123

        # Mock bot
        mock_bot = AsyncMock()
        mock_bot.id = bot_id
        mock_bot.name = "test_bot"
        mock_repo.get_by_id.return_value = mock_bot

        # Execute
        result = await service.stop_bot(bot_id, mock_user)

        # Assert
        assert "status" in result
        assert "bot_name" in result
        mock_repo.get_by_id.assert_called_once_with(bot_id, 1)
        assert (
            mock_event_bus.publish.call_count == 2
        )  # One for mcp_commands, one for bot_events

    @pytest.mark.asyncio
    async def test_restart_bot_success(self, bot_service):
        """Test successful bot restart."""
        service, mock_repo, _, mock_tg_client, mock_event_bus = bot_service

        mock_user = AsyncMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        bot_id = 123

        # Mock bot
        mock_bot = AsyncMock()
        mock_bot.id = bot_id
        mock_bot.name = "test_bot"
        mock_bot.config = {}
        mock_repo.get_by_id.return_value = mock_bot

        # Execute
        result = await service.restart_bot(bot_id, mock_user)

        # Assert
        assert "status" in result
        assert "bot_name" in result
        # Should publish both STOP and START commands
        assert mock_event_bus.publish.call_count == 2
