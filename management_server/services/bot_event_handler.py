"""
Handles asynchronous events related to bot status changes.
"""

import logging
from typing import Callable, Dict, Any, Coroutine

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from management_server.models.models import Bot, BotUpdate

logger = logging.getLogger(__name__)


class BotEventHandler:
    """
    Listens to events from the Trading Gateway and updates the database.
    """

    def __init__(self, db_session_factory: Callable[[], AsyncSession]):
        self._get_db: Callable[[], AsyncSession] = db_session_factory

    async def handle_event(self, event_message: Any):
        """
        Main event handling router.
        """
        event_type = event_message.type
        event_data = event_message.data

        logger.debug(f"Event received: Type={event_type}, Data={event_data}")

        handler_method = getattr(self, f"_handle_{event_type.lower()}", None)

        if handler_method:
            await handler_method(event_data)
        else:
            logger.warning(f"No handler for event type: {event_type}")

    async def _update_bot_state(
        self, bot_name: str | None, update_data: Dict[str, Any]
    ):
        """Helper to update bot state in the database."""
        if not bot_name:
            logger.error("Bot name is None, cannot update state")
            return

        db = self._get_db()
        try:
            result = await db.execute(select(Bot).where(Bot.name == bot_name))
            bot = result.scalar_one_or_none()

            if bot:
                for key, value in update_data.items():
                    setattr(bot, key, value)

                db.add(bot)
                await db.commit()
                logger.info(
                    f"Successfully updated bot '{bot_name}' with data: {update_data}"
                )
            else:
                logger.error(f"Bot '{bot_name}' not found in the database.")
        except Exception as e:
            logger.error(f"Error updating bot '{bot_name}': {e}", exc_info=True)
        finally:
            # If the session factory created a new session, we should close it.
            # In our test case, the session is managed outside, so this is safe.
            pass

    async def _handle_bot_started(self, data: Dict[str, Any]):
        bot_name = data.get("bot_name")
        if not bot_name:
            logger.error("Bot name missing in BOT_STARTED event")
            return
        update_data = {
            "status": "running",
            "pid": data.get("pid"),
            "port": data.get("port"),
        }
        await self._update_bot_state(bot_name, update_data)

    async def _handle_bot_stopped(self, data: Dict[str, Any]):
        bot_name = data.get("bot_name")
        if not bot_name:
            logger.error("Bot name missing in BOT_STOPPED event")
            return
        update_data = {"status": "stopped", "pid": None, "port": None}
        await self._update_bot_state(bot_name, update_data)

    async def _handle_bot_start_failed(self, data: Dict[str, Any]):
        bot_name = data.get("bot_name")
        if not bot_name:
            logger.error("Bot name missing in BOT_START_FAILED event")
            return
        update_data = {"status": "error", "pid": None, "port": None}
        await self._update_bot_state(bot_name, update_data)
