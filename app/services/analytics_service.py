from __future__ import annotations
"""
app/services/analytics_service.py

Aggregate analytics over emotion logs.
"""

from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emotion_log import EmotionLog
from app.models.session import DetectionSession
from app.schemas.emotion import EmotionStats, SessionAnalytics


class AnalyticsService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session_analytics(self, session_id: str) -> SessionAnalytics | None:
        # Fetch session
        s_result = await self.db.execute(
            select(DetectionSession).where(DetectionSession.id == session_id)
        )
        session = s_result.scalar_one_or_none()
        if not session:
            return None

        # Fetch all logs
        l_result = await self.db.execute(
            select(EmotionLog).where(EmotionLog.session_id == session_id)
        )
        logs = list(l_result.scalars().all())

        total = len(logs)
        if total == 0:
            return SessionAnalytics(
                session_id=session_id,
                total_detections=0,
                frame_count=session.frame_count,
                top_emotion=None,
                emotion_distribution=[],
                started_at=session.started_at,
                ended_at=session.ended_at,
            )

        # Count emotions
        counter = Counter(log.dominant_emotion for log in logs)
        top_emotion = counter.most_common(1)[0][0]
        distribution = [
            EmotionStats(
                emotion=emo,
                count=count,
                percentage=round(count / total * 100, 2),
            )
            for emo, count in counter.most_common()
        ]

        return SessionAnalytics(
            session_id=session_id,
            total_detections=total,
            frame_count=session.frame_count,
            top_emotion=top_emotion,
            emotion_distribution=distribution,
            started_at=session.started_at,
            ended_at=session.ended_at,
        )
