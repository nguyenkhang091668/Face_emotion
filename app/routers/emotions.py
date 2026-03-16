"""
app/routers/emotions.py

REST endpoints for sessions and analytics:
  GET  /sessions                → list sessions
  GET  /sessions/{id}           → session detail
  GET  /sessions/{id}/logs      → emotion logs for session
  GET  /sessions/{id}/analytics → aggregated analytics
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.emotion import EmotionLogRead, SessionAnalytics, SessionRead
from app.services.analytics_service import AnalyticsService
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Sessions & Analytics"])


@router.get("", response_model=list[SessionRead])
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    limit: int = 20,
    offset: int = 0,
):
    """List all sessions for the authenticated user."""
    service = SessionService(db)
    uid = None if current_user.is_superuser else current_user.id
    return await service.get_sessions(user_id=uid, limit=limit, offset=offset)


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,
):
    """Get a single session by ID."""
    service = SessionService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.get("/{session_id}/logs", response_model=list[EmotionLogRead])
async def get_session_logs(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,
    limit: int = 200,
):
    """Get all emotion logs for a session."""
    service = SessionService(db)
    return await service.get_logs(session_id, limit=limit)


@router.get("/{session_id}/analytics", response_model=SessionAnalytics)
async def get_analytics(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,
):
    """Get aggregated analytics (emotion distribution) for a session."""
    analytics = await AnalyticsService(db).get_session_analytics(session_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return analytics
