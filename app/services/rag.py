"""RAG service: context retrieval + grounding prompt construction."""
from __future__ import annotations

import logging
from typing import List

from app.config import settings
from app.services.embedder import EmbeddingService
from app.services.vector_store import QdrantService

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are an educational assistant for course content Q&A.

RULES:
1. Answer ONLY based on the provided context below.
2. If the answer is not in the context, say exactly: \
"I don't have enough information in the provided course materials to answer this question."
3. Do NOT use prior knowledge or make assumptions.
4. Quote relevant sections when helpful.
5. Be concise but complete.

These rules ensure students receive accurate information grounded in their course materials."""

# Rough heuristic: ~4 characters per token for truncation budgeting.
_CHARS_PER_TOKEN = 4


class RAGService:
    def __init__(self, embedder: EmbeddingService, vector_store: QdrantService):
        self.embedder = embedder
        self.vector_store = vector_store

    async def retrieve_context(
        self, question: str, collection: str, top_k: int = 5
    ) -> List[str]:
        query_vector = await self.embedder.embed_query(question)
        results = self.vector_store.search(collection, query_vector, top_k)
        return [r["text"] for r in results if r.get("text")]

    def build_prompt(self, question: str, context_chunks: List[str]) -> str:
        budget = settings.max_context_tokens * _CHARS_PER_TOKEN
        selected: List[str] = []
        used = 0
        truncated = False
        for chunk in context_chunks:
            if used + len(chunk) > budget:
                truncated = True
                remaining = budget - used
                if remaining > 0:
                    selected.append(chunk[:remaining])
                break
            selected.append(chunk)
            used += len(chunk)

        if truncated:
            logger.warning("Context truncated to fit %d token budget", settings.max_context_tokens)

        if not selected:
            context = "(no context available)"
        else:
            context = "\n\n---\n\n".join(selected)

        return (
            "=== COURSE MATERIALS CONTEXT ===\n\n"
            f"{context}\n\n"
            "=== END OF CONTEXT ===\n\n"
            f"Student Question: {question}\n\n"
            "Please answer based solely on the context above."
        )
