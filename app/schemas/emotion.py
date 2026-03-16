from __future__ import annotations
"""
app/schemas/emotion.py

Pydantic v2 schemas for emotion detection API responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


#  WebSocket real-time response 

class EmotionResult(BaseModel):
    """Single face detection result returned over WebSocket."""
    box: list[int]           # [x, y, w, h]
    emotion: str
    color: str               # "#RRGGBB"
    scores: dict[str, float]  # top-3 emotions


class FrameResponse(BaseModel):
    """WebSocket message: list of all detected faces in one frame."""
    faces: list[EmotionResult]
    session_id: Optional[str] = None
    frame_number: Optional[int] = None


#  Session schemas 

class SessionCreate(BaseModel):
    user_id: Optional[str] = None


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    frame_count: int


#  Emotion log schemas 

class EmotionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    timestamp: datetime
    dominant_emotion: str
    confidence: Optional[float]
    scores: Optional[dict]
    face_box: Optional[dict]


#  Analytics schemas 

class EmotionStats(BaseModel):
    emotion: str
    count: int
    percentage: float


class SessionAnalytics(BaseModel):
    session_id: str
    total_detections: int
    frame_count: int
    top_emotion: Optional[str]
    emotion_distribution: list[EmotionStats]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
