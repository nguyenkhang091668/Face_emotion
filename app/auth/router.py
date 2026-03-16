"""
app/auth/router.py

Auth API routes:
  POST /auth/register
  POST /auth/login
  POST /auth/refresh
  POST /auth/logout
  GET  /auth/me
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.auth.schemas import (
    MessageResponse,
    Token,
    TokenRefresh,
    UserCreate,
    UserRead,
)
from app.auth.service import AuthService
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


#  POST /auth/register 
@router.post("/register", response_model=UserRead, status_code=201)
async def register(
    data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user account."""
    service = AuthService(db)
    return await service.register(data)


#  POST /auth/login 
@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    OAuth2 password flow login.
    Returns access_token + refresh_token.
    """
    service = AuthService(db)
    return await service.login(form_data.username, form_data.password)


#  POST /auth/refresh 
@router.post("/refresh", response_model=Token)
async def refresh(
    data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Rotate refresh token and issue a new access token."""
    service = AuthService(db)
    return await service.refresh(data.refresh_token)


#  POST /auth/logout 
@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,  # requires authentication
):
    """Revoke the refresh token (logout)."""
    service = AuthService(db)
    await service.logout(data.refresh_token)
    return MessageResponse(message="Successfully logged out")


#  GET /auth/me 
@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    """Return the currently authenticated user's profile."""
    return UserRead.from_orm_user(current_user)
