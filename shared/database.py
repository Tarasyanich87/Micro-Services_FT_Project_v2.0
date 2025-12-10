from management_server.database.connection import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


async def get_database_session():
    """Get database session for local development"""
    async with SessionLocal() as session:
        yield session
