from __future__ import annotations
"""
app/auth/schemas.py

Pydantic v2 request/response schemas for the auth system.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


#  User 

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    roles: list[str] = Field(default_factory=list)
    created_at: datetime

    @classmethod
    def from_orm_user(cls, user) -> "UserRead":
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=user.role_names,
            created_at=user.created_at,
        )


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)


#  Token 

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    refresh_token: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


#  Login 

class LoginRequest(BaseModel):
    """OAuth2 password flow compatible login schema."""
    username: str = Field(..., description="Email address or username")
    password: str


#  Role / Permission 

class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None


#  Generic responses 

class MessageResponse(BaseModel):
    message: str
    success: bool = True
