"""
Authentication service with JWT tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import logging
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.config import settings
from ..database.connection import get_db
from ..models.models import User, UserCreate

logger = logging.getLogger(__name__)

class AuthService:
    """
    Authentication service for user management and JWT tokens.
    """

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.secret_key = settings.JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        Returns User object if authentication successful, None otherwise.
        """
        try:
            result = await self.db.execute(
                select(User).where(User.username == username, User.is_active == True)
            )
            user = result.scalar_one_or_none()

            if not user or not user.verify_password(password):
                return None

            user.last_login = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {e}")
            return None

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        Raises ValueError if user already exists.
        """
        result = await self.db.execute(
            select(User).where(
                (User.username == user_data.username) | (User.email == user_data.email)
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("Username or email already exists")

        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            is_active=True,
            is_superuser=False
        )
        user.set_password(user_data.password)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Created new user: {user.username}")
        return user

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT access token.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token. Returns payload or None if invalid.
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.PyJWTError as e:
            logger.warning(f"Token validation failed: {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Fetch a user by username from the database."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.verify_password(old_password):
            return False

        user.set_password(new_password)
        await self.db.commit()
        logger.info(f"Password changed for user {user.username}")
        return True
