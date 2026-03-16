from __future__ import annotations
"""
app/core/database.py

Async SQLAlchemy engine, session factory, and base ORM class.
Provides get_db() dependency for FastAPI route injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

#  Engine
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_pre_ping=True,
)

#  Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


#  Declarative base
class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


#  FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session per request.
    Rolls back on exception, always closes the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


#  Init tables utility
async def init_db() -> None:
    """Create all tables that don't exist yet (dev / SQLite convenience)."""
    async with engine.begin() as conn:
        # Import all models so Base knows about them
        from app.models import emotion_log, session  # noqa: F401
        from app.auth import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
