"""Dependency providers (singletons)."""
from __future__ import annotations

from functools import lru_cache

from app.services.chunker import ChunkingService
from app.services.parser import FileParser


@lru_cache
def get_parser() -> FileParser:
    return FileParser()


@lru_cache
def get_chunker() -> ChunkingService:
    return ChunkingService()
