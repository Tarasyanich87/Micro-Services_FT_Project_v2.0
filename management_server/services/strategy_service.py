"""
Service for managing strategies stored in the database.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.models import Strategy, StrategyCreate, StrategyUpdate


class StrategyService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_strategies(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[Strategy]:
        """Get a paginated list of strategies for a user."""
        query = select(Strategy).filter(Strategy.created_by == user_id)
        if search:
            query = query.where(Strategy.name.ilike(f"%{search}%"))
        if tag:
            # Assuming tags is a JSON list of strings
            query = query.where(Strategy.tags.contains([tag]))

        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def create_strategy(
        self, strategy_data: StrategyCreate, user_id: int
    ) -> Strategy:
        """Create a new strategy."""
        new_strategy = Strategy(**strategy_data.model_dump(), created_by=user_id)
        self.db.add(new_strategy)
        await self.db.commit()
        await self.db.refresh(new_strategy)
        return new_strategy

    async def get_strategy_by_id(
        self, strategy_id: int, user_id: int
    ) -> Optional[Strategy]:
        """Get a single strategy by its ID."""
        result = await self.db.execute(
            select(Strategy).filter(Strategy.id == strategy_id, Strategy.created_by == user_id)
        )
        return result.scalars().first()

    async def update_strategy(
        self, strategy_id: int, strategy_data: StrategyUpdate, user_id: int
    ) -> Optional[Strategy]:
        """Update an existing strategy."""
        strategy = await self.get_strategy_by_id(strategy_id, user_id)
        if not strategy:
            return None

        update_data = strategy_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(strategy, key, value)

        await self.db.commit()
        await self.db.refresh(strategy)
        return strategy

    async def delete_strategy(self, strategy_id: int, user_id: int) -> bool:
        """Delete a strategy."""
        strategy = await self.get_strategy_by_id(strategy_id, user_id)
        if not strategy:
            return False

        await self.db.delete(strategy)
        await self.db.commit()
        return True
