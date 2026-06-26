# KE HOACH FRONTEND - Multi-LLM RAG API

> **Stack:** React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui
> **Location:** `web/` subfolder trong cung repo BE
> **State:** TanStack Query (fetch/cache), Dexie/IndexedDB (history), recharts (charts), react-router-dom, lucide-react, react-markdown
> **API base:** Vite proxy `->` localhost:8000 (dev); CORS middleware tren BE (prod)

---

## API CONTRACT (tu BE, 8 endpoints)

| Method | Endpoint | Body/Params | Response fields |
|--------|----------|-------------|-----------------|
| GET | `/health` | - | status, version, timestamp |
| GET | `/readiness` | - | status, embedding_model, qdrant, qdrant_url |
| POST | `/documents/upload` | multipart: file, collection, doc_name? | doc_id, collection, source, chunks_created, processing_ms, deduplicated |
| GET | `/collections` | - | collections[], total_collections, total_chunks |
| DELETE | `/collections/{name}` | - | deleted, name, points_removed, deletion_ms |
| POST | `/ask` | {question, collection, provider, top_k?, stream?} | answer, provider, model, latency_ms, chunks_used, total_tokens, context_preview[], collection |
| POST | `/compare` | {question, collection, top_k?} | question, collection, context_chunks, results{groq,gemini,anthropic}, fastest_provider, total_elapsed_ms |
| POST | `/evaluate` | {question, answer, context[], ground_truth?} | faithfulness, answer_relevancy, context_recall?, overall_score, metrics_detail, evaluation_ms |

**Error envelope (all errors):** `{ error, message, status_code, request_id }`
**Error codes:** COLLECTION_NOT_FOUND, DOCUMENT_NOT_FOUND, UNSUPPORTED_FILE_TYPE, DUPLICATE_DOCUMENT, INVALID_COLLECTION_NAME, PROVIDER_UNAVAILABLE, EMBEDDING_MODEL_NOT_READY, CONTEXT_TOO_LARGE, INVALID_PROVIDER, FILE_TOO_LARGE, CONTEXT_EMPTY, INTERNAL_ERROR

---

## SCOPE (7 phase FE + 1 BE prerequisite)

### BE Prerequisite - SSE Streaming cho POST /ask
- Implement `stream=true` -> StreamingResponse SSE (`data: {token}\n\n`)
- Close Backlog issue #17

### FE-1 Scaffold & Design System
- Vite + React + TS + Tailwind + shadcn/ui
- Layout: sidebar nav, dark mode toggle, responsive
- API client typed (types tu BE schemas)
- TanStack Query setup, Vite proxy config
- Dexie/IndexedDB schema (conversations, queries)

### FE-2 Documents & Collections
- Readiness badge (GET /readiness live)
- Collections dashboard: table + delete (GET/DELETE /collections)
- Upload drag-drop (POST /documents/upload) - dedup/409, type error, size limit

### FE-3 Ask + Chat (multi-turn) + SSE
- Multi-turn chat UI (history = IndexedDB via Dexie)
- SSE live token streaming khi stream=true
- Provider selector, top_k slider, context preview, latency display

### FE-4 Compare (Killer Feature)
- 3 side-by-side cards (Groq/Gemini/Anthropic)
- Fastest badge, cost/tokens/latency per provider
- Graceful error card khi 1 provider fail
- Share link + export markdown

### FE-5 Evaluate
- Form (question, answer, context, ground_truth?)
- Metric cards + recharts gauges (faithfulness, relevancy, recall, overall)
- Export markdown report

### FE-6 Analytics
- recharts: compare latency/cost/quality across providers
- Data tu IndexedDB query history
- Provider comparison bar/line charts

### FE-7 Docker & Polish
- docker-compose `web` service (build + nginx serve)
- Responsive mobile polish
- Error-envelope toasts
- README FE quickstart

---

## GITHUB DEPLOYMENT
- Milestone `Frontend` (#7)
- 1 issue BE streaming + 7 issue FE (Tasks + Acceptance Criteria)
- Branch per feature: `feature/fe-1-setup` ... `feature/fe-7-docker-polish`

## LIBS
react, react-dom, react-router-dom, @tanstack/react-query, lucide-react, react-markdown, recharts, dexie, clsx, tailwind-merge, sonner (toasts), shadcn/ui components
