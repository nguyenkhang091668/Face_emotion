from __future__ import annotations
"""
app/auth/dependencies.py

FastAPI dependencies for extracting and validating the current user.
  get_current_user   — requires valid JWT access token
  get_active_user    — additionally checks is_active
  require_role(name) — RBAC guard factory
"""

import logging
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    CredentialsException,
    InactiveUserException,
    PermissionDeniedException,
)
from app.auth.models import User
from app.auth.security import JWTHandler
from app.core.database import get_db

log = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Validate Bearer token and return the associated user."""
    try:
        payload = JWTHandler.decode(token)
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id is None or token_type != JWTHandler.ACCESS_TOKEN_TYPE:
            raise CredentialsException()
    except JWTError:
        raise CredentialsException()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise CredentialsException()
    return user


async def get_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the user account is active."""
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


def require_role(role_name: str):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def _check_role(
        user: Annotated[User, Depends(get_active_user)],
    ) -> User:
        if not user.has_role(role_name) and not user.is_superuser:
            raise PermissionDeniedException(required_role=role_name)
        return user
    return _check_role


#  Typed aliases for cleaner route signatures 
CurrentUser = Annotated[User, Depends(get_active_user)]
