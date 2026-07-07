import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from python_json_logger.json_logger import JsonFormatter # Added import

from app import state
from app.config import settings
from app.errors import (
    RAGAPIException,
    rag_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware import LoggingMiddleware
from app.routers import ask, collections, documents, evaluate, health
from app.services.embedder import EmbeddingService
from app.services.vector_store import QdrantService
from app.services.llm.factory import AVAILABLE_PROVIDERS

# Configure JSON logging
handler = logging.StreamHandler()
formatter = JsonFormatter('%(levelname)s %(asctime)s %(name)s %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(handlers=[handler], level=logging.INFO) # Modified basicConfig
logger = logging.getLogger(__name__)

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload embedding model (skip in tests via RAG_PRELOAD_EMBEDDING=0)
    if os.getenv("RAG_PRELOAD_EMBEDDING", "1") != "0":
        try:
            embedder = EmbeddingService.get_instance()
            embedder.load_model(settings.embedding_model)
            state.AppState.embedding_model_loaded = True

            # Probe Qdrant: get_collections() will raise if not connected
            qdrant_client = QdrantService(url=settings.qdrant_url)
            qdrant_client.client.get_collections()
            state.AppState.qdrant_connected = True

        except Exception as exc:  # pragma: no cover - startup safety net
            logger.warning("Failed to preload embedding model: %s", exc)

    # Validate LLM API keys
    for provider_name in AVAILABLE_PROVIDERS:
        api_key = getattr(settings, f"{provider_name}_api_key", "")
        if not api_key:
            logger.warning(
                "LLM API key for provider '%s' is not set. Requests to this provider may fail.",
                provider_name,
            )

    yield
    # Shutdown (nothing to clean up right now)
    logger.info("Shutting down Multi-LLM RAG API")


app = FastAPI(
    title="Multi-LLM RAG API",
    description="Multi-Provider Retrieval-Augmented Generation API",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware) # Added SlowAPIMiddleware
app.state.limiter = limiter # Added limiter to app state


app.add_exception_handler(RAGAPIException, rag_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health.router)
app.include_router(documents.router, prefix="/api")
app.include_router(collections.router, prefix="/api")
app.include_router(ask.router, prefix="/api")
app.include_router(evaluate.router, prefix="/api")


@app.get("/")
async def root():
    return {"name": "Multi-LLM RAG API", "version": settings.app_version}
