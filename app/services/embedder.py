"""Embedding service: singleton loading the same model once on startup.

CRITICAL: the SAME model must be used for ingestion and queries, otherwise
cosine similarity is meaningless.
"""
from __future__ import annotations

import logging
from typing import List

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class ModelNotLoadedError(RuntimeError):
    pass


class EmbeddingService:
    _instance: "EmbeddingService | None" = None
    _model = None
    _is_loaded: bool = False
    _model_name: str | None = None

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model(self, model_name: str | None = None) -> None:
        """Load the sentence-transformers model. Call ONCE on startup."""
        from sentence_transformers import SentenceTransformer

        name = model_name or settings.embedding_model
        logger.info("Loading embedding model: %s", name)
        self._model = SentenceTransformer(name)
        self._model_name = name
        self._is_loaded = True
        logger.info("Embedding model loaded: %s", name)

    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def model_name(self) -> str | None:
        return self._model_name

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self._is_loaded:
            raise ModelNotLoadedError("Embedding model not loaded yet")
        embeddings = self._model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings).tolist()

    async def embed_query(self, query: str) -> List[float]:
        result = await self.embed_texts([query])
        return result[0]
