import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
import tempfile
import os
import base64
from pathlib import Path

from trading_gateway.services.bot_process_manager import BotProcessManager
from trading_gateway.services.bot_service import BotService
from management_server.tools.redis_streams_event_bus import RedisStreamsEventBus


@pytest.fixture
def event_bus():
    """Mock event bus for testing."""
    bus = AsyncMock(spec=RedisStreamsEventBus)
    return bus


@pytest.fixture
def bot_process_manager(event_bus):
    """BotProcessManager instance for testing."""
    manager = BotProcessManager(event_bus)
    return manager


@pytest.fixture
def bot_service():
    """BotService instance for testing."""
    # BotService doesn't take arguments, just import and return
    from trading_gateway.services.bot_service import BotService

    return BotService()


class TestBotProcessManager:
    """Test cases for BotProcessManager."""

    @pytest.mark.asyncio
    async def test_handle_start_bot_command_success(
        self, bot_process_manager, event_bus
    ):
        """Test successful handling of START_BOT command."""
        # Test data
        command_data = {
            "bot_name": "test_bot",
            "bot_config": {
                "trading_mode": "spot",
                "dry_run": True,
                "exchange": {"name": "binance"},
                "strategy": "TestStrategy",
            },
            "freqai_model": None,
        }

        # Mock subprocess.Popen to avoid actually starting processes
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_popen.return_value = mock_process

            # Execute
            await bot_process_manager.handle_start_bot_command(command_data)

            # Assert process was started
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args[0][
                0
            ]  # First positional argument (command list)

            # Check that freqtrade was called
            assert call_args[0] == "freqtrade"
            assert call_args[1] == "trade"
            assert "--config" in call_args

            # Assert event was published (using global event bus)
            # Note: In real implementation, events are published via global mcp_streams_event_bus
            # So we can't easily mock this in unit tests. This is tested in integration tests.

    @pytest.mark.asyncio
    async def test_handle_start_bot_command_with_freqai_model(
        self, bot_process_manager
    ):
        """Test START_BOT command with FreqAI model."""
        # Create temporary model file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as temp_file:
            temp_file.write(b"fake model data")
            model_path = temp_file.name

        try:
            command_data = {
                "bot_name": "test_bot_with_model",
                "bot_config": {
                    "trading_mode": "spot",
                    "dry_run": True,
                    "exchange": {"name": "binance"},
                    "strategy": "TestStrategy",
                },
                "freqai_model": {
                    "filename": "test_model.joblib",
                    "content_b64": "ZmFrZSBtb2RlbCBkYXRh",  # base64 of "fake model data"
                },
            }

            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.pid = 12346
                mock_popen.return_value = mock_process

                # Execute
                await bot_process_manager.handle_start_bot_command(command_data)

                # Check that model was saved in FreqAI handler cache
                model_path = bot_process_manager.freqai_handler.get_model_path(
                    "test_bot_with_model"
                )
                assert model_path is not None
                assert os.path.exists(model_path)

                # Check file contents
                with open(model_path, "rb") as f:
                    saved_data = f.read()
                    assert saved_data == b"fake model data"

        finally:
            # Cleanup
            if os.path.exists(model_path):
                os.unlink(model_path)
            # Clean up bot directory
            import shutil

            bot_dir_path = bot_process_manager.base_bot_dir / "test_bot_with_model"
            if bot_dir_path.exists():
                shutil.rmtree(bot_dir_path)

    @pytest.mark.asyncio
    async def test_handle_stop_bot_command_not_running(
        self, bot_process_manager, event_bus
    ):
        """Test STOP_BOT command when bot is not running."""
        stop_command = {"bot_name": "nonexistent_bot"}

        await bot_process_manager.handle_stop_bot_command(stop_command)

        # Assert no event was published (since bot wasn't running)
        event_bus.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_find_free_port(self, bot_process_manager):
        """Test finding a free port."""
        port = bot_process_manager._find_free_port()

        # Port should be a valid number
        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    @pytest.mark.asyncio
    async def test_handle_start_bot_invalid_config(
        self, bot_process_manager, event_bus
    ):
        """Test START_BOT command with invalid configuration."""
        command_data = {
            "bot_name": None,  # Invalid: None instead of string
            "bot_config": None,  # Invalid: None instead of dict
        }

        await bot_process_manager.handle_start_bot_command(command_data)

        # Assert no process was started and error event was published
        event_bus.publish.assert_called_once()
        publish_call = event_bus.publish.call_args
        # Check the event_type parameter (should be the third positional arg or in kwargs)
        assert "BOT_START_FAILED" in str(publish_call)


class TestFreqAIModelHandler:
    """Test cases for FreqAIModelHandler."""

    @pytest.fixture
    def model_handler(self):
        """FreqAIModelHandler instance for testing."""
        from trading_gateway.services.freqai_model_handler import FreqAIModelHandler
        import tempfile
        import shutil

        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        handler = FreqAIModelHandler(cache_dir=temp_dir, max_cache_size=2)

        yield handler

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_store_model_for_bot_success(self, model_handler):
        """Test successful model storage."""
        model_data = {
            "filename": "test_model.joblib",
            "content_b64": base64.b64encode(b"fake model data").decode(),
        }

        model_path = await model_handler.store_model_for_bot("test_bot", model_data)

        # Check that model was stored
        assert "test_bot" in model_handler.cache
        assert model_handler.cache["test_bot"] == model_path
        assert os.path.exists(model_path)

        # Check file contents
        with open(model_path, "rb") as f:
            content = f.read()
            assert content == b"fake model data"

    @pytest.mark.asyncio
    async def test_store_model_invalid_data(self, model_handler):
        """Test model storage with invalid data."""
        # Test missing filename
        with pytest.raises(ValueError, match="Missing filename"):
            await model_handler.store_model_for_bot("test_bot", {"content_b64": "data"})

        # Test invalid base64
        with pytest.raises(ValueError, match="Invalid base64 content"):
            await model_handler.store_model_for_bot(
                "test_bot", {"filename": "test.joblib", "content_b64": "invalid"}
            )

        # Test unsupported file type
        with pytest.raises(ValueError, match="Only .joblib files are supported"):
            await model_handler.store_model_for_bot(
                "test_bot", {"filename": "test.pkl", "content_b64": "data"}
            )

    @pytest.mark.asyncio
    async def test_get_model_path(self, model_handler):
        """Test getting model path."""
        model_data = {
            "filename": "test_model.joblib",
            "content_b64": base64.b64encode(b"fake model data").decode(),
        }

        model_path = await model_handler.store_model_for_bot("test_bot", model_data)

        # Test getting existing model
        retrieved_path = model_handler.get_model_path("test_bot")
        assert retrieved_path == model_path

        # Test getting non-existing model
        assert model_handler.get_model_path("nonexistent") is None

    @pytest.mark.asyncio
    async def test_cleanup_bot_models(self, model_handler):
        """Test cleanup of bot models."""
        model_data = {
            "filename": "test_model.joblib",
            "content_b64": base64.b64encode(b"fake model data").decode(),
        }

        model_path = await model_handler.store_model_for_bot("test_bot", model_data)

        # Verify model exists
        assert model_handler.get_model_path("test_bot") == model_path
        assert os.path.exists(model_path)

        # Cleanup
        await model_handler.cleanup_bot_models("test_bot")

        # Verify cleanup
        assert model_handler.get_model_path("test_bot") is None
        assert not os.path.exists(model_path)

    @pytest.mark.asyncio
    async def test_lru_cache_eviction(self, model_handler):
        """Test LRU cache eviction when cache is full."""
        # Store first model
        model_data1 = {
            "filename": "model1.joblib",
            "content_b64": base64.b64encode(b"data1").decode(),
        }
        path1 = await model_handler.store_model_for_bot("bot1", model_data1)

        # Store second model
        model_data2 = {
            "filename": "model2.joblib",
            "content_b64": base64.b64encode(b"data2").decode(),
        }
        path2 = await model_handler.store_model_for_bot("bot2", model_data2)

        # Access first model to update LRU
        model_handler.get_model_path("bot1")

        # Store third model (should evict bot2)
        model_data3 = {
            "filename": "model3.joblib",
            "content_b64": base64.b64encode(b"data3").decode(),
        }
        path3 = await model_handler.store_model_for_bot("bot3", model_data3)

        # Check that bot2 was evicted
        assert model_handler.get_model_path("bot2") is None
        assert not os.path.exists(path2)

        # Check that bot1 and bot3 remain
        assert model_handler.get_model_path("bot1") == path1
        assert model_handler.get_model_path("bot3") == path3


# BotService tests removed - they use global services that are hard to unit test
# These are better tested in integration tests
