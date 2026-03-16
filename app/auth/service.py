from __future__ import annotations
"""
app/auth/service.py

AuthService — business logic layer for user auth operations.
  - register: create user, hash password, assign default role
  - login: validate credentials, issue access + refresh tokens
  - refresh: rotate refresh token, issue new access token
  - logout: revoke refresh token
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    CredentialsException,
    InvalidRefreshTokenException,
    UserAlreadyExistsException,
)
from app.auth.models import RefreshToken, Role, User
from app.auth.schemas import Token, UserCreate, UserRead
from app.auth.security import JWTHandler, PasswordHasher
from app.core.config import settings

log = logging.getLogger(__name__)


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db

    #  Register 

    async def register(self, data: UserCreate) -> UserRead:
        # Check email uniqueness
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise UserAlreadyExistsException(data.email)

        # Hash password
        hashed = PasswordHasher.hash(data.password)

        # Ensure default "viewer" role exists
        role_result = await self.db.execute(select(Role).where(Role.name == "viewer"))
        default_role = role_result.scalar_one_or_none()
        if not default_role:
            default_role = Role(
                name="viewer", description="Default viewer role")
            self.db.add(default_role)
            await self.db.flush()

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hashed,
        )
        user.roles.append(default_role)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        log.info(f"New user registered: {user.email}")
        return UserRead.from_orm_user(user)

    #  Login 

    async def login(self, identifier: str, password: str) -> Token:
        # Find by email or username
        result = await self.db.execute(
            select(User).where(
                (User.email == identifier) | (User.username == identifier)
            )
        )
        user = result.scalar_one_or_none()

        if not user or not PasswordHasher.verify(password, user.hashed_password):
            raise CredentialsException("Incorrect username or password")

        if not user.is_active:
            raise CredentialsException("Inactive account")

        # Issue tokens
        access_token = JWTHandler.create_access_token(
            subject=user.id,
            roles=user.role_names,
        )
        refresh_token_str = JWTHandler.create_refresh_token(subject=user.id)

        # Persist refresh token
        from datetime import timedelta
        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        db_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=expires_at,
        )
        self.db.add(db_token)
        await self.db.flush()

        log.info(f"User logged in: {user.email}")
        return Token(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=JWTHandler.access_token_expiry_seconds(),
        )

    #  Refresh 

    async def refresh(self, refresh_token_str: str) -> Token:
        # Validate token exists in DB and is not revoked
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token_str)
        )
        db_token = result.scalar_one_or_none()

        if not db_token or db_token.revoked:
            raise InvalidRefreshTokenException()

        if db_token.expires_at < datetime.now(tz=timezone.utc):
            raise InvalidRefreshTokenException()

        # Get user
        user_result = await self.db.execute(select(User).where(User.id == db_token.user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            raise InvalidRefreshTokenException()

        # Revoke old token (rotation)
        db_token.revoked = True

        # Issue new tokens
        access_token = JWTHandler.create_access_token(
            subject=user.id,
            roles=user.role_names,
        )
        new_refresh = JWTHandler.create_refresh_token(subject=user.id)

        from datetime import timedelta
        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_db_token = RefreshToken(
            token=new_refresh,
            user_id=user.id,
            expires_at=expires_at,
        )
        self.db.add(new_db_token)
        await self.db.flush()

        log.info(f"Token refreshed for user: {user.email}")
        return Token(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=JWTHandler.access_token_expiry_seconds(),
        )

    #  Logout 

    async def logout(self, refresh_token_str: str) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token_str)
        )
        db_token = result.scalar_one_or_none()
        if db_token:
            db_token.revoked = True
            await self.db.flush()
        log.info("User logged out (refresh token revoked)")
