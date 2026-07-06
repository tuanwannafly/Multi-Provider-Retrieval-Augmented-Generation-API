"""Qdrant vector store: collection lifecycle, upsert, search, dedup, stats."""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from cachetools import cached, TTLCache # Added import

logger = logging.getLogger(__name__)

# Cache for collection info to optimize repeated calls
_COLLECTIONS_CACHE = TTLCache(maxsize=64, ttl=5) # Added cache

class QdrantService:
    def __init__(self, url: str, vector_size: int = 384):
        self.client = QdrantClient(url=url)
        self.vector_size = vector_size

    def collection_exists(self, collection_name: str) -> bool:
        existing = [c.name for c in self.client.get_collections().collections]
        return collection_name in existing

    def ensure_collection(self, collection_name: str) -> None:
        if not self.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=Distance.COSINE
                ),
            )
            logger.info("Created Qdrant collection: %s", collection_name)

    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        doc_id: str,
        source: str,
    ) -> int:
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}:{idx}"))
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "doc_id": doc_id,
                        "source": source,
                        "chunk_index": idx,
                        "text": chunk,
                        "collection": collection_name,
                    },
                )
            )
        self.client.upsert(collection_name=collection_name, points=points)
        _COLLECTIONS_CACHE.clear() # Clear cache on upsert
        return len(points)

    def search(
        self, collection_name: str, query_vector: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    def check_duplicate(self, collection_name: str, doc_id: str) -> bool:
        if not self.collection_exists(collection_name):
            return False
        try:
            points, _ = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                ),
                limit=1,
            )
            return len(points) > 0
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("check_duplicate failed: %s", exc)
            return False

    def count_points(self, collection_name: str) -> int:
        info = self.client.count(
            collection_name=collection_name, exact=True
        )
        return info.count

    def distinct_doc_ids(self, collection_name: str) -> List[str]:
        doc_ids: set[str] = set()
        offset: Optional[int] = None
        # Bounded scroll to get an approximate count for display, not a full scan
        limit_per_scroll = 100 # Adjusted limit
        total_scrolled = 0
        while True:
            points, offset = self.client.scroll(
                collection_name=collection_name,
                limit=limit_per_scroll,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                doc_id = (point.payload or {}).get("doc_id")
                if doc_id:
                    doc_ids.add(doc_id)
            total_scrolled += len(points)
            if offset is None or total_scrolled >= 1000: # Added total_scrolled limit
                break
        return list(doc_ids)

    @cached(_COLLECTIONS_CACHE) # Added cache
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        info = self.client.get_collection(collection_name)
        vector_size = self.vector_size
        try:
            configured = info.config.params.vectors
            size = getattr(configured, "size", None)
            if size:
                vector_size = size
        except Exception:  # pragma: no cover
            pass
        chunk_count = info.points_count or self.count_points(collection_name)
        return {
            "name": collection_name,
            "document_count": len(self.distinct_doc_ids(collection_name)),
            "chunk_count": chunk_count,
            "vector_size": vector_size,
            "created_at": None,
            "disk_size_mb": None,
        }

    @cached(_COLLECTIONS_CACHE) # Added cache
    def list_collections(self) -> List[Dict[str, Any]]:
        names = [c.name for c in self.client.get_collections().collections]
        return [self.get_collection_info(name) for name in names]

    def delete_collection(self, collection_name: str) -> int:
        info = self.get_collection_info(collection_name)
        removed = info["chunk_count"]
        self.client.delete_collection(collection_name=collection_name)
        _COLLECTIONS_CACHE.clear() # Clear cache on delete
        return removed