"""
Database connection management with SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging
from ..models.base import Base
from typing import AsyncGenerator
import os
from fastapi import Depends

from ..core.config import settings

logger = logging.getLogger(__name__)

# Create engine based on database URL
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
        future=True,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        echo=settings.DEBUG,
        future=True,
    )

# Create async session factory
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db(
    db_session: AsyncSession = Depends(lambda: SessionLocal()),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        Database session
    """
    try:
        yield db_session
    finally:
        await db_session.close()


async def init_database() -> None:
    """
    Initialize database tables and run migrations.
    """
    try:
        logger.info("Initializing database...")

        # Import all models to ensure they are registered
        from ..models.models import Base, User, Bot, Strategy

        # Create tables
        async with engine.begin() as conn:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created")

        # Run initial data setup
        await _setup_initial_data()

        logger.info("✅ Database initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


async def close_database() -> None:
    """
    Close database connections.
    """
    try:
        logger.info("Closing database connections...")
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")


async def _setup_initial_data() -> None:
    """
    Setup initial data (admin user, default strategies, etc.)
    """
    try:
        async with engine.begin() as conn:
            # Check if admin user exists
            result = await conn.execute(
                text("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            )
            admin_exists = result.scalar()

            if not admin_exists:
                logger.info("Creating default admin user...")
                # Create default admin user
                from ..models.models import User

                admin = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="System Administrator",
                    is_active=True,
                    is_superuser=True,
                )
                admin.set_password("admin123")  # Change in production!

                await conn.run_sync(lambda session: session.add(admin))
                logger.info("✅ Default admin user created")

    except Exception as e:
        logger.warning(f"Failed to setup initial data: {e}")


# Synchronous session for Celery tasks
if settings.DATABASE_URL.startswith("sqlite"):
    sync_engine = create_engine(
        settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"),
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    sync_engine = create_engine(
        settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"),
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        echo=settings.DEBUG,
    )

SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
