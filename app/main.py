import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.errors import (
    RAGAPIException,
    rag_exception_handler,
    validation_exception_handler,
)
from app.routers import documents, health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-LLM RAG API",
    description="Multi-Provider Retrieval-Augmented Generation API",
    version=settings.app_version,
)

app.add_exception_handler(RAGAPIException, rag_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(health.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    return {"name": "Multi-LLM RAG API", "version": settings.app_version}
