"""Dependency providers (singletons)."""
from __future__ import annotations

import secrets
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.services.chunker import ChunkingService
from app.services.embedder import EmbeddingService
from app.services.evaluator import RAGEvaluator
from app.services.parser import FileParser
from app.services.rag import RAGService
from app.services.vector_store import QdrantService
from app.config import settings

# API Key header for authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@lru_cache
def get_parser() -> FileParser:
    return FileParser()


@lru_cache
def get_chunker() -> ChunkingService:
    return ChunkingService()


def get_embedder() -> EmbeddingService:
    return EmbeddingService.get_instance()


@lru_cache
def get_vector_store() -> QdrantService:
    return QdrantService(url=settings.qdrant_url, vector_size=settings.qdrant_collection_dim)


def get_rag_service() -> RAGService:
    return RAGService(embedder=get_embedder(), vector_store=get_vector_store())


def get_evaluator() -> RAGEvaluator:
    return RAGEvaluator(embedder=get_embedder())


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    Optional API key authentication. If RAG_API_KEY is set,
    requests must include a matching X-API-Key header.
    """
    if settings.rag_api_key:
        if not api_key or not secrets.compare_digest(api_key, settings.rag_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key",
            )