# Real-time Emotion Detection API

> Production-grade DS pipeline: MTCNN + DeepFace + FastAPI + JWT Auth + PostgreSQL

## ️ Architecture

```
app/
 core/           # Config, DB engine, Logging
 auth/           # JWT + RBAC (User / Role / Permission / RefreshToken)
 pipeline/       # ML pipeline (preprocessor → detector → tracker → analyzer)
 models/         # SQLAlchemy ORM (DetectionSession, EmotionLog)
 schemas/        # Pydantic v2 API schemas
 services/       # Business logic (SessionService, AnalyticsService)
 routers/        # REST endpoints (sessions, analytics)
 static/         # WebSocket browser client

alembic/            # Database migrations
tests/
 conftest.py     # Shared fixtures
 integration/    # Auth + Pipeline tests
 e2e/            # Full API + WS tests
docs/               # PRD, ADR, System Design
monitoring/         # Prometheus config
```

##  Quick Start

```bash
# 1. Clone and setup
cp .env.example .env      # edit SECRET_KEY and DATABASE_URL

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run DB migrations
alembic upgrade head

# 4. Start the API
uvicorn app.main:app --reload
```

Visit:

- **UI**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

##  Docker

```bash
# Full stack (app + PostgreSQL + Prometheus + Grafana)
docker-compose up -d
```

##  Tests

```bash
make test          # Run all tests
make test-cov      # Run with HTML coverage report
```

| Test Type   | Count  |
| ----------- | ------ |
| E2E         | 13     |
| Integration | 26     |
| **Total**   | **39** |

##  API Endpoints

| Method | Endpoint                 | Auth | Description                  |
| ------ | ------------------------ | ---- | ---------------------------- |
| POST   | /auth/register           | —    | Register new user            |
| POST   | /auth/login              | —    | Login (OAuth2 password flow) |
| POST   | /auth/refresh            | —    | Rotate refresh token         |
| POST   | /auth/logout             |    | Revoke refresh token         |
| GET    | /auth/me                 |    | Current user profile         |
| GET    | /sessions                |    | List sessions                |
| GET    | /sessions/{id}           |    | Session detail               |
| GET    | /sessions/{id}/logs      |    | Emotion logs                 |
| GET    | /sessions/{id}/analytics |    | Emotion distribution stats   |
| WS     | /ws                      | —    | Real-time emotion detection  |
| GET    | /health                  | —    | Health check                 |

## ️ Tech Stack

- **Framework**: FastAPI + Uvicorn
- **ML**: MTCNN, DeepFace (TF-Keras)
- **Database**: SQLAlchemy async + SQLite (dev) / PostgreSQL (prod)
- **Migrations**: Alembic
- **Auth**: JWT HS256 (python-jose) + bcrypt (cost 12)
- **Validation**: Pydantic v2
- **Testing**: pytest + pytest-asyncio + httpx
- **CI/CD**: GitHub Actions → GHCR
- **Monitoring**: Prometheus + Grafana

##  Make Targets

```bash
make dev          # Start dev server with hot-reload
make test         # Run pytest
make lint         # Ruff linter
make migrate      # alembic upgrade head
make docker-up    # docker-compose up -d
make clean        # Clean artefacts
```
