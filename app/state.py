"""Shared application runtime state (model readiness, etc.)."""
from __future__ import annotations


class AppState:
    """Mutable flags populated during the FastAPI lifespan."""

    embedding_model_loaded: bool = False
    qdrant_connected: bool = False

    @classmethod
    def ready(cls) -> bool:
        return cls.embedding_model_loaded and cls.qdrant_connected
