"""Optional RAGAS integration. Falls back gracefully when ragas is not installed.

Usage:
    result = await evaluate_with_ragas(question, answer, contexts, ground_truth)
    if result is None:
        # fall back to custom metrics (app.services.evaluator.RAGEvaluator)

To enable:  pip install ragas
"""
from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - depends on optional dependency
    from ragas import evaluate as ragas_evaluate
    from ragas.metrics import (
        answer_relevancy as ragas_answer_relevancy,
        context_recall as ragas_context_recall,
        faithfulness as ragas_faithfulness,
    )

    RAGAS_AVAILABLE = True
except Exception:  # pragma: no cover
    RAGAS_AVAILABLE = False
    ragas_evaluate = None
    ragas_faithfulness = None
    ragas_answer_relevancy = None
    ragas_context_recall = None


def is_available() -> bool:
    return RAGAS_AVAILABLE


async def evaluate_with_ragas(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None,
) -> Optional[dict]:
    """Run real RAGAS evaluation. Returns None when RAGAS is unavailable."""
    if not RAGAS_AVAILABLE:
        logger.info("RAGAS not installed; falling back to custom metrics")
        return None

    import asyncio

    from datasets import Dataset  # type: ignore

    metrics = [ragas_faithfulness, ragas_answer_relevancy]
    if ground_truth:
        metrics.append(ragas_context_recall)

    record = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
    }
    if ground_truth:
        record["ground_truth"] = [ground_truth]

    dataset = Dataset.from_dict(record)

    def _run():
        return ragas_evaluate(dataset=dataset, metrics=metrics)

    try:
        scores = await asyncio.to_thread(_run)
    except Exception as exc:  # pragma: no cover - RAGAS runtime errors
        logger.warning("RAGAS evaluation failed: %s", exc)
        return None

    result = {key: float(val) for key, val in dict(scores).items()}
    logger.info("RAGAS evaluation complete: %s", result)
    return result
