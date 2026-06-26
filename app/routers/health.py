"""Health & readiness endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app import state
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/readiness")
async def readiness():
    return {
        "status": "ready" if state.AppState.ready() else "starting",
        "embedding_model": "loaded" if state.AppState.embedding_model_loaded else "not_loaded",
        "qdrant": "connected" if state.AppState.qdrant_connected else "disconnected",
        "qdrant_url": settings.qdrant_url,
    }
