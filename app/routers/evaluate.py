"""Evaluation endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import get_embedder, get_evaluator
from app.errors import RAGAPIException
from app.models.schemas import EvaluateRequest
from app.services.embedder import EmbeddingService, ModelNotLoadedError
from app.services.evaluator import RAGEvaluator

router = APIRouter(tags=["evaluation"])


@router.post("/evaluate")
async def evaluate(
    request: EvaluateRequest,
    evaluator: RAGEvaluator = Depends(get_evaluator),
):
    try:
        result = await evaluator.evaluate(
            question=request.question,
            answer=request.answer,
            context=request.context,
            ground_truth=request.ground_truth,
        )
    except ModelNotLoadedError:
        raise RAGAPIException(
            code="EMBEDDING_MODEL_NOT_READY",
            message="Embedding model is not loaded yet. Try again shortly.",
            status_code=503,
        )
    return result
