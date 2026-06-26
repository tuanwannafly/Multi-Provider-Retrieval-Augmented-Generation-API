"""Lightweight fakes for testing the RAG pipeline without heavy deps or network."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional


class FakeEmbedder:
    """Deterministic embedder producing 384-dim pseudo-vectors from text hash."""

    def __init__(self):
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._vector(t) for t in texts]

    async def embed_query(self, query: str) -> List[float]:
        return self._vector(query)

    def _vector(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Stretch 32 bytes into 384 floats in [0, 1].
        values: List[float] = []
        for i in range(384):
            values.append(digest[i % len(digest)] / 255.0)
        return values


class FakeVectorStore:
    def __init__(self):
        # collection_name -> {"points": [payload, ...], "ids": set(doc_id)}
        self._collections: Dict[str, Dict[str, Any]] = {}

    def ensure_collection(self, name: str) -> None:
        self._collections.setdefault(name, {"points": [], "ids": set()})

    def collection_exists(self, name: str) -> bool:
        return name in self._collections

    def check_duplicate(self, name: str, doc_id: str) -> bool:
        return name in self._collections and doc_id in self._collections[name]["ids"]

    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        doc_id: str,
        source: str,
    ) -> int:
        self.ensure_collection(collection_name)
        for idx, chunk in enumerate(chunks):
            self._collections[collection_name]["points"].append(
                {
                    "doc_id": doc_id,
                    "source": source,
                    "chunk_index": idx,
                    "text": chunk,
                    "collection": collection_name,
                    "score": 1.0,
                }
            )
        self._collections[collection_name]["ids"].add(doc_id)
        return len(chunks)

    def search(self, name: str, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        self.ensure_collection(name)
        points = self._collections[name]["points"]
        return [
            {"text": p["text"], "score": p["score"], "payload": p}
            for p in points[:top_k]
        ]

    def count_points(self, name: str) -> int:
        return len(self._collections.get(name, {"points": []})["points"])

    def distinct_doc_ids(self, name: str) -> List[str]:
        return list(self._collections.get(name, {"ids": set()})["ids"])

    def get_collection_info(self, name: str) -> Dict[str, Any]:
        self.ensure_collection(name)
        return {
            "name": name,
            "document_count": len(self._collections[name]["ids"]),
            "chunk_count": self.count_points(name),
            "vector_size": 384,
            "created_at": None,
            "disk_size_mb": None,
        }

    def list_collections(self) -> List[Dict[str, Any]]:
        return [self.get_collection_info(n) for n in self._collections]

    def delete_collection(self, name: str) -> int:
        removed = self.count_points(name)
        self._collections.pop(name, None)
        return removed
