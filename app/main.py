from __future__ import annotations
"""
app/main.py — FastAPI application entry point (refactored)

Registers all routers, handles lifespan (DB init + model warm-up),
and configures CORS / middleware.

Endpoints overview:
  GET  /             → WebSocket UI (index.html)
  GET  /health       → health check
  WS   /ws           → real-time emotion detection stream
  POST /auth/...     → authentication
  GET  /sessions/... → session & analytics REST API
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.pipeline.orchestrator import PipelineOrchestrator
from app.routers.emotions import router as sessions_router

#  Logging 
setup_logging()
log = logging.getLogger(__name__)

#  Pipeline singleton (one per process) 
_pipeline: PipelineOrchestrator | None = None


#  Lifespan context 
@asynccontextmanager
async def lifespan(application: FastAPI):
    global _pipeline
    log.info("  Starting up …")

    # Initialise DB tables
    log.info("️   Initialising database …")
    await init_db()
    log.info("  Database ready.")

    # Warm up ML models
    log.info("  Loading MTCNN + DeepFace models …")
    _pipeline = PipelineOrchestrator()
    log.info("  Pipeline ready.")

    yield

    log.info("  Shutting down.")
    _pipeline = None


#  FastAPI app 
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time Emotion Detection API with JWT auth and analytics",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

#  CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  Static files 
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

#  Routers 
app.include_router(auth_router)
app.include_router(sessions_router)


#  Routes 

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the WebSocket emotion detection UI."""
    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>UI not found — place index.html in app/static/</h1>")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "pipeline_loaded": _pipeline is not None,
    }


#  WebSocket emotion endpoint 

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket: receive JPEG frame bytes, return JSON emotion results.
    Protocol:
      Client → server : raw JPEG bytes
      Server → client : {"faces": [{box, emotion, color, scores}, ...]}
    """
    await ws.accept()
    client = ws.client
    log.info(f"  WS connected: {client}")

    try:
        while True:
            data = await ws.receive_bytes()

            if _pipeline is None:
                await ws.send_text(json.dumps({"faces": [], "error": "Pipeline not ready"}))
                continue

            # Run pipeline in thread pool (CPU-bound, don't block the event loop)
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, _pipeline.process_bytes, data)

            await ws.send_text(json.dumps({"faces": results}))

    except WebSocketDisconnect:
        log.info(f"  WS disconnected: {client}")
    except Exception as exc:
        log.exception(f"WS error: {exc}")
