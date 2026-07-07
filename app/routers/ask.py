"""RAG query endpoints: POST /ask (single provider) and POST /compare (killer feature)."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from slowapi.ext.fastapi import Limiter, get_remote_address # Added import
from app.main import limiter # Import limiter from app.main

from app.config import settings
from app.deps import get_rag_service, verify_api_key # Added verify_api_key
from app.errors import RAGAPIException
from app.models.schemas import AskRequest, AskResponse, CompareRequest, CompareResponse, CompareResult
from app.services.llm.base import ProviderUnavailableError
from app.services.llm.factory import AVAILABLE_PROVIDERS, get_provider
from app.services.rag import RAG_SYSTEM_PROMPT, RAGService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rag"])


async def _retrieve(rag: RAGService, question: str, collection: str, top_k: int):
    if not rag.vector_store.collection_exists(collection):
        raise RAGAPIException(
            code="COLLECTION_NOT_FOUND",
            message=f"Collection '{collection}' does not exist. Upload documents first.",
            status_code=404,
        )
    chunks = await rag.retrieve_context(question, collection, top_k)
    if not chunks:
        raise RAGAPIException(
            code="CONTEXT_EMPTY",
            message=f"No retrievable context found in collection '{collection}'.",
            status_code=404,
        )
    return chunks


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit(settings.rate_limit_ask) # Added rate limit
async def ask(request: AskRequest, rag: RAGService = Depends(get_rag_service)):
    chunks = await _retrieve(rag, request.question, request.collection, request.top_k)
    prompt = rag.build_prompt(request.question, chunks)

    provider = get_provider(request.provider)

    # Streaming path: Server-Sent Events
    if request.stream:
        return await _ask_stream(provider, prompt, request, chunks)

    # Non-streaming path: single JSON response
    try:
        result = await asyncio.wait_for(
            provider.complete(prompt, system=RAG_SYSTEM_PROMPT),
            timeout=settings.llm_timeout_seconds,
        )
    except asyncio.TimeoutError:
        raise RAGAPIException(
            code="PROVIDER_UNAVAILABLE",
            message=f"{request.provider} request timed out after {settings.llm_timeout_seconds}s",
            status_code=503,
        )
    except ProviderUnavailableError as exc:
        raise RAGAPIException(
            code="PROVIDER_UNAVAILABLE",
            message=str(exc),
            status_code=503,
        )

    return {
        "answer": result.answer,
        "provider": provider.name,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "chunks_used": len(chunks),
        "total_tokens": result.tokens,
        "context_preview": [c[:200] for c in chunks[:2]],
        "collection": request.collection,
    }


async def _ask_stream(
    provider, prompt: str, request: AskRequest, chunks: list[str]
) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        start = time.monotonic()
        try:
            async for token in provider.complete_stream(
                prompt, system=RAG_SYSTEM_PROMPT
            ):
                yield _sse({"token": token})
            latency_ms = int((time.monotonic() - start) * 1000)
            yield _sse(
                {
                    "done": True,
                    "provider": provider.name,
                    "model": provider.model_id,
                    "latency_ms": latency_ms,
                    "chunks_used": len(chunks),
                    "collection": request.collection,
                }
            )
        except ProviderUnavailableError as exc:
            yield _sse({"error": "PROVIDER_UNAVAILABLE", "message": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("ask stream failed")
            yield _sse({"error": "STREAM_ERROR", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/compare", response_model=CompareResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit(settings.rate_limit_compare) # Added rate limit
async def compare(request: CompareRequest, rag: RAGService = Depends(get_rag_service)):
    chunks = await _retrieve(rag, request.question, request.collection, request.top_k)
    prompt = rag.build_prompt(request.question, chunks)

    start = time.monotonic()

    async def call_provider(name: str):
        try:
            provider = get_provider(name)
            result = await asyncio.wait_for(
                provider.complete(prompt, system=RAG_SYSTEM_PROMPT),
                timeout=settings.llm_timeout_seconds,
            )
            return name, CompareResult(
                answer=result.answer,
                model=result.model,
                latency_ms=result.latency_ms,
                tokens=result.tokens,
                estimated_cost_usd=result.estimated_cost_usd,
                status="success",
            )
        except asyncio.TimeoutError:
            return name, CompareResult(
                status="error",
                error="TIMEOUT",
                message=f"Request timed out after {settings.llm_timeout_seconds}s",
                latency_ms=settings.llm_timeout_seconds * 1000,
            )
        except ProviderUnavailableError as exc:
            return name, CompareResult(status="error", error="PROVIDER_ERROR", message=str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("compare: provider %s failed", name)
            return name, CompareResult(status="error", error="UNKNOWN", message=str(exc))

    raw_results = await asyncio.gather(*(call_provider(p) for p in AVAILABLE_PROVIDERS))
    results = dict(raw_results)
    total_ms = int((time.monotonic() - start) * 1000)

    fastest = None
    for name, payload in results.items():
        if isinstance(payload, CompareResult) and payload.status == "success":
            if fastest is None or payload.latency_ms < results[fastest].latency_ms:
                fastest = name


    return CompareResponse(
        question=request.question,
        collection=request.collection,
        context_chunks=len(chunks),
        results=results,
        fastest_provider=fastest,
        total_elapsed_ms=total_ms,
    )