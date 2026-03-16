# System Design: Real-time Emotion Detection

**Version**: 1.0.0 | **Date**: 2026-03-16

---

## 1. System Overview

```
Browser
    JPEG bytes (WebSocket)
  ▼
FastAPI /ws
  
  ► PipelineOrchestrator
         FramePreprocessor  (decode, resize)
         FaceDetector       (MTCNN, 0.5x downscale)
         FaceTracker        (centroid matching, deque history)
         EmotionAnalyzer    (DeepFace, background thread)
    JSON {faces: [...]}
  ▼
Browser (canvas overlay)

REST API  ← JWT Bearer token   Browser
   /auth/*         (AuthService → DB)
   /sessions/*     (SessionService, AnalyticsService → DB)
```

## 2. Database Schema

```
users < user_roles > roles < role_permissions > permissions
users < refresh_tokens
users < detection_sessions < emotion_logs
```

### Key tables

| Table              | Purpose                                    |
| ------------------ | ------------------------------------------ |
| users              | Accounts with hashed password, active flag |
| roles              | Named roles (viewer, analyst, admin)       |
| permissions        | Fine-grained action permissions            |
| refresh_tokens     | Revocable long-lived tokens                |
| detection_sessions | Camera session metadata per user           |
| emotion_logs       | Per-frame emotion detection records        |

## 3. ML Pipeline Data Flow

```
raw_bytes
  → FramePreprocessor.decode()     → BGR ndarray
  → FramePreprocessor.resize()     → bounded ndarray
  → FaceDetector.detect()          → [(x,y,w,h), ...]
  → FaceTracker.update()           → tracked identities
  → EmotionAnalyzer.analyze_async()→ callback → tracker.add_emotion()
  → FaceTracker.get_results()      → [{box, emotion, scores}, ...]
  → [{"box","emotion","color","scores"}, ...]  → JSON → client
```

## 4. API Contracts (key)

**POST /auth/login** → `{ access_token, refresh_token, token_type, expires_in }`

**WS /ws**

- Client sends: raw JPEG bytes
- Server sends: `{ "faces": [{ "box":[x,y,w,h], "emotion":"happy", "color":"#00DC5A", "scores":{...} }] }`

**GET /sessions/{id}/analytics** → `{ emotion_distribution: [{emotion, count, percentage}], top_emotion, frame_count }`

## 5. Configuration Matrix

| Setting                     | Dev (SQLite)     | Prod (PostgreSQL)  |
| --------------------------- | ---------------- | ------------------ |
| DATABASE_URL                | sqlite+aiosqlite | postgresql+asyncpg |
| DEBUG                       | true             | false              |
| ENVIRONMENT                 | development      | production         |
| LOG FORMAT                  | human-readable   | JSON               |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30               | 30                 |
| ANALYZE_EVERY_N_FRAMES      | 6                | 6                  |
