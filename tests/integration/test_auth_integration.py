"""
tests/integration/test_auth_integration.py

Integration tests for the Auth system (≥ 15 tests).
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


#  Registration 

async def test_register_success(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "Password123!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient, registered_user):
    resp = await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "anotheruser",
        "password": "Password123!",
    })
    assert resp.status_code == 409


async def test_register_short_password(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "short@test.com",
        "username": "shortpw",
        "password": "123",
    })
    assert resp.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "not-an-email",
        "username": "bademail",
        "password": "Password123!",
    })
    assert resp.status_code == 422


#  Login 

async def test_login_success(client: AsyncClient, registered_user):
    resp = await client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


async def test_login_wrong_password(client: AsyncClient, registered_user):
    resp = await client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post("/auth/login", data={
        "username": "ghost@test.com",
        "password": "TestPass123!",
    })
    assert resp.status_code == 401


async def test_login_by_username(client: AsyncClient, registered_user):
    resp = await client.post("/auth/login", data={
        "username": "testuser",
        "password": "TestPass123!",
    })
    assert resp.status_code == 200


#  Token Refresh 

async def test_refresh_success(client: AsyncClient, auth_token_pair):
    resp = await client.post("/auth/refresh", json={
        "refresh_token": auth_token_pair["refresh_token"]
    })
    assert resp.status_code == 200
    new_data = resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    # Token rotation: new refresh token must differ from old
    assert new_data["refresh_token"] != auth_token_pair["refresh_token"]


async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post("/auth/refresh", json={
        "refresh_token": "this.is.not.valid"
    })
    assert resp.status_code == 401


async def test_refresh_used_token_rejected(client: AsyncClient, auth_token_pair):
    """After rotating, the old refresh token must be revoked."""
    old_token = auth_token_pair["refresh_token"]
    # Use it once
    await client.post("/auth/refresh", json={"refresh_token": old_token})
    # Second use should fail
    resp = await client.post("/auth/refresh", json={"refresh_token": old_token})
    assert resp.status_code == 401


#  /auth/me 

async def test_get_me_authenticated(client: AsyncClient, auth_headers):
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data


async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


#  Logout 

async def test_logout_success(client: AsyncClient, auth_headers, auth_token_pair):
    resp = await client.post(
        "/auth/logout",
        json={"refresh_token": auth_token_pair["refresh_token"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


async def test_logout_requires_auth(client: AsyncClient, auth_token_pair):
    resp = await client.post(
        "/auth/logout",
        json={"refresh_token": auth_token_pair["refresh_token"]},
    )
    assert resp.status_code == 401
