from typing import List, Optional

from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from management_server.models.models import Bot, BotCreate, BotUpdate


class BotRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, bot_id: int, user_id: int) -> Optional[Bot]:
        result = await self.db_session.execute(
            select(Bot).filter(Bot.id == bot_id, Bot.created_by == user_id)
        )
        return result.scalars().first()

    async def get_by_name(self, bot_name: str) -> Optional[Bot]:
        result = await self.db_session.execute(
            select(Bot).filter(Bot.name == bot_name)
        )
        return result.scalars().first()

    async def get_all(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Bot]:
        result = await self.db_session.execute(
            select(Bot).filter(Bot.created_by == user_id).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, bot_data: BotCreate, user_id: int) -> Bot:
        new_bot = Bot(**bot_data.model_dump(), created_by=user_id)
        self.db_session.add(new_bot)
        await self.db_session.commit()
        await self.db_session.refresh(new_bot)
        return new_bot

    async def update(self, bot_id: int, bot_data: BotUpdate, user_id: int) -> Optional[Bot]:
        update_data = bot_data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(bot_id, user_id)

        await self.db_session.execute(
            sqlalchemy_update(Bot)
            .where(Bot.id == bot_id, Bot.created_by == user_id)
            .values(**update_data)
        )
        await self.db_session.commit()
        return await self.get_by_id(bot_id, user_id)

    async def delete(self, bot_id: int, user_id: int) -> bool:
        result = await self.db_session.execute(
            sqlalchemy_delete(Bot).where(Bot.id == bot_id, Bot.created_by == user_id)
        )
        await self.db_session.commit()
        return result.rowcount > 0

    async def update_bot_status(self, bot_id: int, status: str) -> Optional[Bot]:
        await self.db_session.execute(
            sqlalchemy_update(Bot).where(Bot.id == bot_id).values(status=status)
        )
        await self.db_session.commit()
        # Note: This doesn't check user_id, assuming it's an internal system update
        result = await self.db_session.execute(select(Bot).filter(Bot.id == bot_id))
        return result.scalars().first()
