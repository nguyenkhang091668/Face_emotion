"""
tests/conftest.py

Pytest fixtures for the Emotion Detection test suite.
- in-memory SQLite async DB
- async test client (httpx)
- auth helper to get Bearer tokens
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

#  Test DB (in-memory SQLite) 
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all DB tables once per test session."""
    async with test_engine.begin() as conn:
        from app.auth import models  # noqa: F401
        from app.models import session, emotion_log  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test DB session with rollback after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test client wired to use the test DB session."""
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


#  Auth helpers 

@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register and return a test user dict."""
    resp = await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123!",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, registered_user: dict) -> dict:
    """Login and return Authorization headers."""
    resp = await client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_token_pair(client: AsyncClient, registered_user: dict) -> dict:
    """Return full token pair (access + refresh)."""
    resp = await client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!",
    })
    return resp.json()
