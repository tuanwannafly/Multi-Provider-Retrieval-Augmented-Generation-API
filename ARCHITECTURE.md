# Architecture & Design Decisions

## Overview

This project implements a **Multi-Provider RAG (Retrieval-Augmented Generation) API** with three LLM providers (Groq, Gemini, Anthropic) behind a unified abstraction layer. The standout feature is `POST /api/compare`, which benchmarks all three providers in parallel.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│              (Frontend App · Postman · curl)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP REST
┌─────────────────────────▼───────────────────────────────────────┐
│                       FastAPI APPLICATION                       │
│   /api/documents   /api/ask   /api/api/compare   /api/evaluate   /api/collections    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FileParser · Chunker · EmbeddingService · RAGService    │  │
│  │  LLM Providers (Groq/Gemini/Anthropic) · Evaluator       │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────┬────────────────────────────────┬─────────────────────┘
           │                                │
┌──────────▼──────────────┐    ┌────────────▼────────────────────┐
│   Qdrant Vector DB      │    │         LLM PROVIDERS           │
│   (port 6333)           │    │  Groq · Gemini · Anthropic      │
└─────────────────────────┘    └─────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Why Qdrant instead of Chroma/Pinecone?

**Decision:** Qdrant for vector storage.

**Rationale:**
- **Payload filtering**: Qdrant supports filtering on metadata fields (e.g., `collection`, `doc_id`) at query time, essential for multi-tenant RAG.
- **Collection isolation**: Each collection is a true namespace, not just a filter.
- **Production-ready**: Built-in health checks, persistence, and REST API.
- **Self-hosted**: No vendor lock-in; runs locally via Docker.

**Tradeoff:** Slightly more complex setup than Chroma, but worth it for production features.

---

### 2. Why local embeddings (`all-MiniLM-L6-v2`) instead of OpenAI?

**Decision:** Use `sentence-transformers/all-MiniLM-L6-v2` (384-dim, local inference).

**Rationale:**
- **Zero API cost**: No per-call charges for embeddings.
- **Fully portable**: Works offline; no external dependency.
- **Fast**: 384-dim vectors are 4x smaller than OpenAI's 1536-dim, reducing storage and query latency.
- **Quality**: Good enough for educational content retrieval.

**Tradeoff:** Slightly lower retrieval quality than OpenAI `text-embedding-3-large`, but the cost/quality balance favors local for this portfolio project.

**Critical invariant:** The SAME model MUST be used for ingestion and queries. Changing the model after ingestion breaks cosine similarity. This is enforced via the `EMBEDDING_MODEL` env var and documented prominently.

---

### 3. Why NOT use full LangChain chains?

**Decision:** Use only `RecursiveCharacterTextSplitter` from LangChain; implement LLM routing manually.

**Rationale:**
- **Abstraction leakage**: Full LangChain chains hide the logic; reviewers can't see the skill.
- **Debug complexity**: When a chain fails, tracing the issue is hard.
- **Portfolio value**: Writing the LLM routing layer demonstrates senior-level understanding of async orchestration, error handling, and provider abstraction.

**Tradeoff:** More code to maintain, but the educational value and interview impact are worth it.

---

### 4. Why custom eval metrics instead of just RAGAS?

**Decision:** Implement custom RAGAS-style metrics (faithfulness, answer_relevancy, context_recall) as the primary path; RAGAS is optional.

**Rationale:**
- **Dependency risk**: RAGAS has complex dependencies and may fail to install on some systems.
- **Understanding demonstration**: Implementing cosine-similarity-based metrics shows understanding of the underlying math.
- **Graceful fallback**: If RAGAS isn't installed, the app still works with custom metrics.

**Tradeoff:** Custom metrics are simpler than RAGAS's NLI-based approach, but still produce meaningful scores (>0.8 faithfulness on grounded answers).

---

### 5. Why `asyncio.gather()` for `/api/compare`?

**Decision:** Use `asyncio.gather()` with per-provider `asyncio.wait_for()` timeouts.

**Rationale:**
- **Parallelism**: All three providers are queried concurrently, not sequentially. Total time ≈ max(individual latencies), not sum.
- **Graceful degradation**: Individual `try/except` ensures one provider's failure doesn't crash the whole request.
- **Clear winner**: `fastest_provider` field shows which provider responded quickest.

**Tradeoff:** More complex error handling, but the UX benefit (side-by-side comparison in <15s) is significant.

---

### 6. Why preload the embedding model on startup?

**Decision:** Load `sentence-transformers` model in the FastAPI lifespan event, blocking readiness until loaded.

**Rationale:**
- **Predictable latency**: First request doesn't incur a 5-10s cold start penalty.
- **Fail-fast**: If the model can't load (e.g., disk full), the app doesn't start, making the issue visible immediately.
- **Readiness probe**: `GET /readiness` returns `"status": "ready"` only after the model is loaded and Qdrant is connected, enabling Kubernetes readiness probes.

**Tradeoff:** Longer startup time, but production systems should prioritize request latency over startup time.

---

### 7. Error Envelope Consistency

**Decision:** All errors follow a strict envelope:
```json
{
  "error": "COLLECTION_NOT_FOUND",
  "message": "Human-readable description",
  "status_code": 404,
  "request_id": "req_abc123"
}
```

**Rationale:**
- **Client-friendly**: Clients can parse `error` code programmatically.
- **Debugging**: `request_id` correlates logs across services.
- **Professionalism**: Consistent error handling signals production readiness.

---

## Data Flow: Ingestion Pipeline

```
[User Upload PDF]
       │
       ▼
[SHA256 Hash] → doc_id = "sha256:abc123..."
       │
       ▼
[pypdf extracts text per page]
       │
       ▼
[RecursiveCharacterTextSplitter]
       │ chunk_size=512, overlap=50
       ▼
[EmbeddingService.encode() via asyncio.to_thread()] → 384-dim vectors
       │
       ▼
[QdrantService.check_duplicate(doc_id)]
       │ if exists → return 409 DUPLICATE_DOCUMENT
       ▼
[QdrantService.upsert_chunks()]
       │ point_id = uuid5(doc_id:chunk_index)
       │ payload = {doc_id, source, chunk_index, text, collection}
       ▼
[Response: {"doc_id", "chunks_created", "processing_ms"}]
```

**Deterministic IDs:** `uuid5(namespace, f"{doc_id}:{chunk_index}")` ensures idempotent upserts—re-uploading the same file produces the same point IDs.

---

## Data Flow: Query Pipeline

```
[User: POST /api/ask {"question", "collection", "provider"}]
       │
       ▼
[EmbeddingService.embed_query() via asyncio.to_thread()] → query_vector[384]
       │
       ▼
[QdrantService.search(collection, query_vector, top_k=5)]
       │ filter: payload.collection == requested_collection
       │ return: [(text, score, payload), ...]
       │
       ▼
[RAGService.build_prompt(question, chunks)]
       │ Context cap: 4000 tokens (~16000 chars)
       │ Truncate from end if overflow
       ▼
[LLMProvider.complete(prompt, system=RAG_SYSTEM_PROMPT)]
       │ Timeout: 15s default
       │ ProviderUnavailableError → 503
       ▼
[Response: {"answer", "provider", "latency_ms", "chunks_used", ...}]
```

**Critical:** The query embedding MUST use the same model as ingestion. Mismatched models produce meaningless cosine similarities.

---

## Security Considerations

- **Optional API Key Auth**: `RAG_API_KEY` environment variable protects sensitive endpoints.
- **No secrets in code**: All API keys come from `.env` (gitignored).
- **File size limits**: `max_upload_size_mb=20` prevents DoS via large uploads.
- **Collection name validation**: Regex `^[a-z0-9_-]{1,64}$` prevents injection attacks.
- **Error messages**: Generic error messages for 500s prevent leaking internal details (e.g., stack traces) to clients.

---

## Scalability Notes

Current design is single-instance. To scale horizontally:
1. **Shared Qdrant**: Run Qdrant as a separate service (already Dockerized).
2. **Stateless API**: Multiple API containers behind a load balancer; no local state.
3. **Redis cache** (future): Cache frequent query results to reduce LLM calls.
4. **Async embedding queue** (future): Offload embedding generation to a background worker (Celery/RQ).

---

## Future Enhancements (Backlog)

| Feature | Priority | Notes |
|---------|----------|-------|
| Streaming SSE for `/api/ask` | Medium | `stream=true` → Server-Sent Events |
| Per-request cost tracking | Low | Token count × model pricing |
| DELETE `/api/documents/{doc_id}` | Low | Delete single doc, not whole collection |
| Semantic chunking | Low | Chunk by meaning, not character count |
| API key auth + rate limiting | Medium | Multi-tenant readiness |

---

*This document reflects the architecture as of v1.0.0. Changes will be documented here with version timestamps.*