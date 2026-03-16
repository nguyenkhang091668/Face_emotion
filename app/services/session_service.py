from __future__ import annotations
"""
app/services/session_service.py

CRUD operations for DetectionSession and EmotionLog.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emotion_log import EmotionLog
from app.models.session import DetectionSession

log = logging.getLogger(__name__)


class SessionService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: Optional[str] = None) -> DetectionSession:
        session = DetectionSession(user_id=user_id)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        log.info(f"Session created: {session.id}")
        return session

    async def end_session(self, session_id: str) -> Optional[DetectionSession]:
        result = await self.db.execute(
            select(DetectionSession).where(DetectionSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.ended_at = datetime.now(tz=timezone.utc)
            await self.db.flush()
        return session

    async def increment_frame(self, session_id: str) -> None:
        result = await self.db.execute(
            select(DetectionSession).where(DetectionSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.frame_count += 1

    async def log_emotion(
        self,
        session_id: str,
        dominant_emotion: str,
        scores: dict,
        face_box: dict,
        confidence: Optional[float] = None,
    ) -> EmotionLog:
        entry = EmotionLog(
            session_id=session_id,
            dominant_emotion=dominant_emotion,
            confidence=confidence,
            scores=scores,
            face_box=face_box,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_sessions(
        self, user_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> list[DetectionSession]:
        q = select(DetectionSession).order_by(
            DetectionSession.started_at.desc())
        if user_id:
            q = q.where(DetectionSession.user_id == user_id)
        q = q.limit(limit).offset(offset)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def get_session(self, session_id: str) -> Optional[DetectionSession]:
        result = await self.db.execute(
            select(DetectionSession).where(DetectionSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_logs(self, session_id: str, limit: int = 200) -> list[EmotionLog]:
        result = await self.db.execute(
            select(EmotionLog)
            .where(EmotionLog.session_id == session_id)
            .order_by(EmotionLog.timestamp.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
