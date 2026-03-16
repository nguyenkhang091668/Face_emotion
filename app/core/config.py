from __future__ import annotations
"""
app/core/config.py

Centralised Pydantic-Settings configuration.
All values are read from environment variables or .env file.
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    #  Application 
    APP_NAME: str = "Emotion Detection API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    #  Database 
    DATABASE_URL: str = "sqlite+aiosqlite:///./emotion_detection.db"

    #  JWT 
    SECRET_KEY: str = "change-this-secret-key-in-production-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    #  CORS 
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", "http://localhost:8000"]

    #  Server 
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    #  ML Pipeline 
    ANALYZE_EVERY_N_FRAMES: int = 6
    SMOOTH_WINDOW: int = 8
    CENTROID_THRESH: int = 80
    DETECTOR_BACKEND: str = "mtcnn"
    FACE_CONFIDENCE_THRESHOLD: float = 0.85

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton pattern)."""
    return Settings()


# Module-level convenience alias
settings = get_settings()
