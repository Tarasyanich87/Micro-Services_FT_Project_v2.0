"""
Authentication endpoints.
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ...auth.service import AuthService
from ...auth.dependencies import get_current_user, get_current_active_user
from ...models.models import User, UserLogin, TokenResponse, UserResponse, UserCreate
from ...core.config import settings

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Used for Swagger UI and similar tools.
    """
    user = await service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = service.create_access_token(
        data={"sub": user.username, "type": "access"}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user=UserResponse.model_validate(user)
    )

@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    login_data: UserLogin,
    service: AuthService = Depends()
) -> Any:
    """
    JSON-based login endpoint for frontend applications.
    """
    user = await service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = service.create_access_token(
        data={"sub": user.username, "type": "access"}
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user=UserResponse.model_validate(user)
    )

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    service: AuthService = Depends()
) -> Any:
    """
    Register a new user account.
    """
    try:
        user = await service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information.
    """
    return UserResponse.model_validate(current_user)

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends()
) -> Any:
    """
    Change current user password.
    """
    success = await service.change_password(
        current_user.id, old_password, new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change failed. Check old password."
        )

    return {"message": "Password changed successfully"}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout current user (client-side token removal).
    This is a placeholder endpoint. In a stateless JWT system,
    logout is primarily handled on the client-side by deleting the token.
    """
    return {"message": "Logged out successfully"}
