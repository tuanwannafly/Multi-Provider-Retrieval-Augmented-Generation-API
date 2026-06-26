import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app import state
from app.config import settings
from app.errors import (
    RAGAPIException,
    rag_exception_handler,
    validation_exception_handler,
)
from app.routers import ask, collections, documents, health
from app.services.embedder import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload embedding model (skip in tests via RAG_PRELOAD_EMBEDDING=0)
    if os.getenv("RAG_PRELOAD_EMBEDDING", "1") != "0":
        try:
            embedder = EmbeddingService.get_instance()
            embedder.load_model(settings.embedding_model)
            state.AppState.embedding_model_loaded = True
        except Exception as exc:  # pragma: no cover - startup safety net
            logger.warning("Failed to preload embedding model: %s", exc)
    yield
    # Shutdown (nothing to clean up right now)
    logger.info("Shutting down Multi-LLM RAG API")


app = FastAPI(
    title="Multi-LLM RAG API",
    description="Multi-Provider Retrieval-Augmented Generation API",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_exception_handler(RAGAPIException, rag_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(collections.router)
app.include_router(ask.router)


@app.get("/")
async def root():
    return {"name": "Multi-LLM RAG API", "version": settings.app_version}
