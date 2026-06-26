"""Dependency providers (singletons)."""
from __future__ import annotations

from functools import lru_cache

from app.services.chunker import ChunkingService
from app.services.embedder import EmbeddingService
from app.services.parser import FileParser
from app.services.vector_store import QdrantService
from app.config import settings


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
