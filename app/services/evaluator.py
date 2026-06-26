"""Custom RAGAS-style evaluation metrics (primary path, no heavy deps).

Metrics:
  - faithfulness: fraction of answer sentences supported by the context
  - answer_relevancy: cosine similarity between embedded question and answer
  - context_recall: fraction of ground-truth sentences covered by context (optional)
"""
from __future__ import annotations

import logging
import time
from typing import List, Optional

import numpy as np

from app.services.embedder import EmbeddingService

logger = logging.getLogger(__name__)

_FAITHFULNESS_THRESHOLD = 0.7
_CONTEXT_RECALL_THRESHOLD = 0.65


def _split_sentences(text: str, min_len: int = 20) -> List[str]:
    parts = [s.strip() for s in text.split(".") if s.strip()]
    return [s for s in parts if len(s) >= min_len]


class RAGEvaluator:
    def __init__(self, embedder: EmbeddingService):
        self.embedder = embedder

    async def evaluate(
        self,
        question: str,
        answer: str,
        context: List[str],
        ground_truth: Optional[str] = None,
    ) -> dict:
        from sklearn.metrics.pairwise import cosine_similarity

        start = time.monotonic()

        faithfulness = await self._faithfulness(answer, context, cosine_similarity)
        answer_relevancy = await self._answer_relevancy(question, answer, cosine_similarity)

        metrics_detail = {
            "faithfulness": {
                "description": "Fraction of answer statements supported by context",
                "method": "NLI decomposition (cosine sim)",
                "score": faithfulness,
            },
            "answer_relevancy": {
                "description": "Cosine similarity between embedded question and answer",
                "method": "cosine(embed(Q), embed(A))",
                "score": answer_relevancy,
            },
        }

        context_recall: Optional[float] = None
        if ground_truth:
            context_recall = await self._context_recall(
                context, ground_truth, cosine_similarity
            )
            weights = {"faithfulness": 0.4, "answer_relevancy": 0.4, "context_recall": 0.2}
        else:
            weights = {"faithfulness": 0.5, "answer_relevancy": 0.5}

        scores = {"faithfulness": faithfulness, "answer_relevancy": answer_relevancy}
        if context_recall is not None:
            scores["context_recall"] = context_recall
            metrics_detail["context_recall"] = {
                "description": "Ground truth sentences covered by retrieved context",
                "method": "sentence overlap ratio",
                "score": context_recall,
                "requires_ground_truth": True,
            }

        overall = sum(scores[k] * weights[k] for k in scores)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "faithfulness": round(faithfulness, 4),
            "answer_relevancy": round(answer_relevancy, 4),
            "context_recall": round(context_recall, 4) if context_recall is not None else None,
            "overall_score": round(overall, 4),
            "metrics_detail": metrics_detail,
            "evaluation_ms": elapsed_ms,
        }

    async def _faithfulness(self, answer: str, context: List[str], cosine_fn) -> float:
        answer_sentences = _split_sentences(answer)
        if not answer_sentences:
            return 1.0
        full_context = " ".join(context)
        if not full_context.strip():
            return 0.0
        embeddings = await self.embedder.embed_texts(answer_sentences + [full_context])
        sentence_embeds = np.asarray(embeddings[:-1])
        context_embed = np.asarray(embeddings[-1:])
        similarities = cosine_fn(sentence_embeds, context_embed).flatten()
        supported = int(np.sum(similarities >= _FAITHFULNESS_THRESHOLD))
        return float(supported / len(answer_sentences))

    async def _answer_relevancy(self, question: str, answer: str, cosine_fn) -> float:
        embeddings = await self.embedder.embed_texts([question, answer])
        q = np.asarray(embeddings[0:1])
        a = np.asarray(embeddings[1:2])
        return float(cosine_fn(q, a)[0][0])

    async def _context_recall(
        self, context: List[str], ground_truth: str, cosine_fn
    ) -> float:
        gt_sentences = _split_sentences(ground_truth, min_len=10)
        if not gt_sentences:
            return 1.0
        full_context = " ".join(context)
        if not full_context.strip():
            return 0.0
        embeddings = await self.embedder.embed_texts(gt_sentences + [full_context])
        gt_embeds = np.asarray(embeddings[:-1])
        ctx_embed = np.asarray(embeddings[-1:])
        similarities = cosine_fn(gt_embeds, ctx_embed).flatten()
        covered = int(np.sum(similarities >= _CONTEXT_RECALL_THRESHOLD))
        return float(covered / len(gt_sentences))
