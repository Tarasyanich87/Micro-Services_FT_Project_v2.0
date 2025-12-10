"""
Database service for common CRUD operations.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
import logging

from .connection import async_session

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DatabaseService:
    """
    Generic database service for CRUD operations.
    """

    @property
    def session(self) -> AsyncSession:
        """Get database session."""
        return async_session()

    async def get_by_id(self, model_class: Type[T], id: int) -> Optional[T]:
        """Get record by ID."""
        async with self.session as session:
            result = await session.execute(
                select(model_class).where(model_class.id == id)
            )
            return result.scalar_one_or_none()

    async def get_all(self, model_class: Type[T], skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination."""
        async with self.session as session:
            result = await session.execute(
                select(model_class).offset(skip).limit(limit)
            )
            return result.scalars().all()

    async def create(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """Create new record."""
        async with self.session as session:
            try:
                instance = model_class(**data)
                session.add(instance)
                await session.commit()
                await session.refresh(instance)
                return instance
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error creating {model_class.__name__}: {e}")
                raise ValueError(f"Record already exists or invalid data")

    async def update(self, model_class: Type[T], id: int, data: Dict[str, Any]) -> Optional[T]:
        """Update record by ID."""
        async with self.session as session:
            try:
                result = await session.execute(
                    select(model_class).where(model_class.id == id)
                )
                instance = result.scalar_one_or_none()

                if not instance:
                    return None

                for key, value in data.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)

                await session.commit()
                await session.refresh(instance)
                return instance

            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating {model_class.__name__} {id}: {e}")
                raise

    async def delete(self, model_class: Type[T], id: int) -> bool:
        """Delete record by ID."""
        async with self.session as session:
            try:
                result = await session.execute(
                    select(model_class).where(model_class.id == id)
                )
                instance = result.scalar_one_or_none()

                if not instance:
                    return False

                await session.delete(instance)
                await session.commit()
                return True

            except Exception as e:
                await session.rollback()
                logger.error(f"Error deleting {model_class.__name__} {id}: {e}")
                raise

    async def count(self, model_class: Type[T]) -> int:
        """Count total records."""
        async with self.session as session:
            result = await session.execute(
                select(func.count()).select_from(model_class)
            )
            return result.scalar()
