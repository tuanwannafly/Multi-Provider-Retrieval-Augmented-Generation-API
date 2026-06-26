"""Collection management endpoints."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.deps import get_vector_store
from app.errors import RAGAPIException
from app.services.vector_store import QdrantService

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("")
async def list_collections(vector_store: QdrantService = Depends(get_vector_store)):
    collections = vector_store.list_collections()
    total_chunks = sum(c["chunk_count"] for c in collections)
    return {
        "collections": collections,
        "total_collections": len(collections),
        "total_chunks": total_chunks,
    }


@router.delete("/{name}")
async def delete_collection(name: str, vector_store: QdrantService = Depends(get_vector_store)):
    if not vector_store.collection_exists(name):
        raise RAGAPIException(
            code="COLLECTION_NOT_FOUND",
            message=f"Collection '{name}' does not exist",
            status_code=404,
        )
    start = time.monotonic()
    removed = vector_store.delete_collection(name)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    return {
        "deleted": True,
        "name": name,
        "points_removed": removed,
        "deletion_ms": elapsed_ms,
    }
