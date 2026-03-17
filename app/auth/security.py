from __future__ import annotations
"""
app/auth/security.py

PasswordHasher  — bcrypt with cost-12
JWTHandler      — HS256 access + refresh tokens (python-jose)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

#  Password hashing

import uuid


class PasswordHasher:
    _ctx = CryptContext(schemes=["bcrypt"],
                        deprecated="auto", bcrypt__rounds=12)

    @classmethod
    def hash(cls, plain: str) -> str:
        return cls._ctx.hash(plain)

    @classmethod
    def verify(cls, plain: str, hashed: str) -> bool:
        return cls._ctx.verify(plain, hashed)


#  JWT token handler

class JWTHandler:
    ACCESS_TOKEN_TYPE = "access"
    REFRESH_TOKEN_TYPE = "refresh"

    @classmethod
    def _create_token(
        cls,
        subject: str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(tz=timezone.utc)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
            "jti": str(uuid.uuid4()),
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @classmethod
    def create_access_token(
        cls,
        subject: str,
        roles: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        delta = expires_delta or timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        claims = {"roles": roles or []}
        return cls._create_token(subject, cls.ACCESS_TOKEN_TYPE, delta, claims)

    @classmethod
    def create_refresh_token(
        cls,
        subject: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        delta = expires_delta or timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return cls._create_token(subject, cls.REFRESH_TOKEN_TYPE, delta)

    @classmethod
    def decode(cls, token: str) -> dict[str, Any]:
        """Decode and verify a JWT. Raises JWTError on failure."""
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    @classmethod
    def get_subject(cls, token: str) -> str | None:
        try:
            payload = cls.decode(token)
            return payload.get("sub")
        except JWTError:
            return None

    @classmethod
    def access_token_expiry_seconds(cls) -> int:
        return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
