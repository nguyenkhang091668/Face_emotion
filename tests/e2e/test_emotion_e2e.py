"""
tests/e2e/test_emotion_e2e.py

End-to-end tests for the full API surface:
  health check, WebSocket emotion stream, sessions REST API.
"""

import json

import cv2
import numpy as np
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


#  Health

async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


async def test_docs_available(client: AsyncClient):
    resp = await client.get("/docs")
    assert resp.status_code == 200


async def test_root_serves_html(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


#  Sessions REST API

async def test_list_sessions_authenticated(client: AsyncClient, auth_headers):
    resp = await client.get("/sessions", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_sessions_unauthenticated(client: AsyncClient):
    resp = await client.get("/sessions")
    assert resp.status_code == 401


async def test_get_session_not_found(client: AsyncClient, auth_headers):
    resp = await client.get("/sessions/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_session_analytics_not_found(client: AsyncClient, auth_headers):
    resp = await client.get("/sessions/nonexistent-id/analytics", headers=auth_headers)
    assert resp.status_code == 404


#  WebSocket

def test_websocket_empty_frame():
    """Sending invalid bytes to /ws should return empty faces, not crash."""
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as test_client:
        with test_client.websocket_connect("/ws") as ws:
            ws.send_bytes(b"invalid frame data")
            data = json.loads(ws.receive_text())
            assert "faces" in data
            assert isinstance(data["faces"], list)


def test_websocket_blank_jpeg():
    """Blank JPEG image should be processed without error."""
    from fastapi.testclient import TestClient
    from app.main import app
    # Create a small black image encoded as JPEG
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    raw_bytes = buf.tobytes()

    with TestClient(app) as test_client:
        with test_client.websocket_connect("/ws") as ws:
            ws.send_bytes(raw_bytes)
            data = json.loads(ws.receive_text())
            assert "faces" in data
            # Empty image has no faces — that's fine
            assert isinstance(data["faces"], list)


def test_websocket_multiple_frames():
    """Should handle multiple sequential frames."""
    from fastapi.testclient import TestClient
    from app.main import app
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    raw_bytes = buf.tobytes()

    with TestClient(app) as test_client:
        with test_client.websocket_connect("/ws") as ws:
            for _ in range(3):
                ws.send_bytes(raw_bytes)
                resp = json.loads(ws.receive_text())
                assert "faces" in resp


#  Auth complete flow

async def test_full_auth_flow(client: AsyncClient):
    """Register → Login → Get /me → Logout."""
    # Register
    r = await client.post("/auth/register", json={
        "email": "e2e_flow@test.com",
        "username": "e2euser",
        "password": "E2ePassword1!",
    })
    assert r.status_code == 201

    # Login
    r = await client.post("/auth/login", data={
        "username": "e2e_flow@test.com",
        "password": "E2ePassword1!",
    })
    assert r.status_code == 200
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # /me
    r = await client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "e2e_flow@test.com"

    # Logout
    r = await client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert r.status_code == 200
