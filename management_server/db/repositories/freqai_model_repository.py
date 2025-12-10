"""
Repository for FreqAI models.
"""
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ...models.models import FreqAIModel

class FreqAIModelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, model_id: int, user_id: int) -> Optional[FreqAIModel]:
        """Get a FreqAI model by its ID, ensuring it belongs to the user."""
        result = await self.db.execute(
            select(FreqAIModel).where(FreqAIModel.id == model_id, FreqAIModel.created_by == user_id)
        )
        return result.scalar_one_or_none()
