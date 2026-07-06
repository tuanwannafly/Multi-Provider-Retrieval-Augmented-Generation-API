# Multi-Provider Retrieval-Augmented Generation API

A production-grade **RAG (Retrieval-Augmented Generation) API** built with FastAPI, Qdrant, and an abstraction layer over three LLM providers (**Groq, Gemini, Anthropic**). Its standout feature is `POST /api/compare`, which queries all three providers in parallel and returns a side-by-side benchmark.

> Built as a portfolio project demonstrating RAG expertise, multi-LLM orchestration, evaluation metrics, and production mindset.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│              (Postman · curl · Frontend App)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP REST
┌─────────────────────────▼───────────────────────────────────────┐
│                       FastAPI APPLICATION                       │
│   /api/documents   /api/ask   /api/compare   /api/evaluate   /api/collections       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FileParser · Chunker · EmbeddingService · RAGService    │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────┬────────────────────────────────┬─────────────────────┘
           │                                │
┌──────────▼──────────────┐    ┌────────────▼────────────────────┐
│   Qdrant Vector DB      │    │         LLM PROVIDERS           │
│   (port 6333)           │    │  Groq · Gemini · Anthropic      │
└─────────────────────────┘    └─────────────────────────────────┘
```

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for design decisions and tradeoffs.

---

## 5-Minute Quickstart

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose)
- API keys: [Groq](https://console.groq.com) (free) · [Gemini](https://aistudio.google.com) (free) · [Anthropic](https://console.anthropic.com)

### 1. Clone & configure
```bash
git clone https://github.com/tuanwannafly/Multi-Provider-Retrieval-Augmented-Generation-API.git
cd Multi-Provider-Retrieval-Augmented-Generation-API
cp .env.example .env
# Edit .env and fill in GROQ_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY, RAG_API_KEY (optional)
```

### 2. Start services
```bash
docker compose up --build -d

# Wait for readiness (embedding model preloads on startup)
curl http://localhost:8000/readiness
# {"status":"ready","embedding_model":"loaded","qdrant":"connected", ...}
```

### 3. Seed demo data
```bash
docker compose exec api python scripts/seed_demo_data.py
```

### 4. Try it
```bash
# Single-provider RAG query (using /api/ prefix)
curl -X POST "http://localhost:8000/api/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is gradient descent?","collection":"dl-intro","provider":"groq"}'

# KILLER FEATURE: compare all 3 providers in parallel (using /api/ prefix)
curl -X POST "http://localhost:8000/api/compare" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is supervised learning?","collection":"ml-basics"}'

# Evaluate answer quality (RAGAS-style metrics) (using /api/ prefix)
curl -X POST "http://localhost:8000/api/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is gradient descent?","answer":"Gradient descent is an optimizer.","context":["Gradient descent minimizes a loss function."]}'
```

OpenAPI docs are auto-generated at http://localhost:8000/docs.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Ingest PDF/DOCX/TXT into a collection |
| `GET`  | `/api/collections` | List collections with stats |
| `DELETE` | `/api/collections/{name}` | Delete a collection |
| `POST` | `/api/ask` | RAG query with a single provider |
| `POST` | `/api/compare` | **Killer feature**: 3 providers in parallel |
| `POST` | `/api/evaluate` | RAGAS-style quality metrics |
| `GET`  | `/health` | Liveness (root path) |
| `GET`  | `/readiness` | Model + Qdrant readiness (root path) |

### Error Envelope
All errors follow a consistent shape:
```json
{ "error": "COLLECTION_NOT_FOUND", "message": "...", "status_code": 404, "request_id": "req_..." }
```

---

## Frontend Application (web/)

This project includes a React/Vite/TypeScript/Tailwind frontend application located in the `web/` directory. It provides a user interface to interact with the RAG API.

### Running the Frontend

**Development Mode:**
```bash
cd web
npm install
npm run dev
# Access at http://localhost:3000 (Vite dev server proxies API calls to backend)
```

**Docker Compose (Production-like):**
When running `docker compose up`, the frontend is served by an Nginx container. Access it at `http://localhost:3000` (or the port configured in `docker-compose.yml`). Nginx handles routing API calls to the backend service.

---

## Key Design Decisions
- **Local embeddings** (`all-MiniLM-L6-v2`, 384-dim) — zero API cost, fully portable.
- **No full LangChain chain** — only the text splitter; the LLM routing layer is hand-written to demonstrate understanding.
- **Custom eval metrics** as the primary path (cosine similarity), with optional RAGAS integration.
- **Graceful degradation**: `POST /api/compare` returns `200` even if one provider fails.
- **API Key Authentication**: Optional `RAG_API_KEY` for securing endpoints.
- **Frontend Integration**: Served by Nginx in a separate Docker service, communicating with the backend via `/api` prefix.

Details in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Development
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# Start only Qdrant, run API locally with hot-reload
docker compose up qdrant -d
QDRANT_URL=http://localhost:6333 uvicorn app.main:app --reload --port 8000

# Run frontend in dev mode
cd web
npm install
npm run dev
cd ..

# Run tests
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Stack
FastAPI · Qdrant · LangChain (text splitters only) · sentence-transformers · Groq · Gemini · Anthropic · Docker Compose · React · Vite · TypeScript · Tailwind CSS
