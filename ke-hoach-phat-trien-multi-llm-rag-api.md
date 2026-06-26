# KẾ HOẠCH PHÁT TRIỂN SẢN PHẨM
# Multi-LLM RAG API

> **Dự án:** Multi-Provider Retrieval-Augmented Generation API  
> **Mục tiêu:** Portfolio project cho Edtronaut internship application  
> **Thời gian:** 5 ngày (40 giờ)  
> **Stack chính:** FastAPI · Qdrant · LangChain · Groq · Gemini · Anthropic · Docker Compose  

---

## MỤC LỤC

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Mục tiêu sản phẩm](#2-mục-tiêu-sản-phẩm)
3. [Stakeholders & Yêu cầu](#3-stakeholders--yêu-cầu)
4. [Kiến trúc hệ thống](#4-kiến-trúc-hệ-thống)
5. [Technology Stack](#5-technology-stack)
6. [API Contract đầy đủ](#6-api-contract-đầy-đủ)
7. [Kế hoạch phát triển theo Phase](#7-kế-hoạch-phát-triển-theo-phase)
8. [Cấu trúc thư mục dự án](#8-cấu-trúc-thư-mục-dự-án)
9. [Schema & Data Models](#9-schema--data-models)
10. [Risk Management](#10-risk-management)
11. [KPIs & Định nghĩa thành công](#11-kpis--định-nghĩa-thành-công)
12. [Roadmap tương lai](#12-roadmap-tương-lai)
13. [Hướng dẫn triển khai](#13-hướng-dẫn-triển-khai)

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1 Bối cảnh kinh doanh

Edtronaut là một edtech company với core asset là **educational content** — bao gồm PDF slides, tài liệu học tập, transcript bài giảng. Thách thức trực tiếp của họ là:

- Học viên không thể tìm kiếm thông tin nhanh từ lượng tài liệu khổng lồ
- Câu trả lời từ LLM thuần túy thường hallucinate, không bám vào nội dung khóa học
- Không có cơ chế đo lường chất lượng output của AI

Project này giải quyết đúng 3 pain points đó thông qua một **RAG API production-grade** với khả năng so sánh đa nhà cung cấp LLM trong thời gian thực.

### 1.2 Giá trị cốt lõi

| Giá trị | Mô tả |
|---------|-------|
| **RAG Accuracy** | Câu trả lời được grounded hoàn toàn vào document content, không hallucinate |
| **Multi-LLM Routing** | Abstraction layer cho phép chuyển đổi linh hoạt giữa Groq, Gemini, Anthropic |
| **Eval Metrics** | RAGAS-style metrics đo lường faithfulness, relevancy, context recall |
| **Benchmarking** | POST /compare — feature độc đáo so sánh 3 providers song song, real-time |

### 1.3 Tại sao dự án này nổi bật?

Hầu hết intern portfolio chỉ implement RAG với 1 provider duy nhất. Project này đi xa hơn với:

- **Multi-provider abstraction layer** (3 providers, 1 interface)
- **Built-in LLM benchmarking** — tính năng mà hầu hết production systems cần nhưng ít ai build vào portfolio
- **Evaluation endpoint** với RAGAS metrics — thể hiện hiểu biết về AI quality assurance
- **Production-ready setup** với Docker Compose, multi-stage Dockerfile, health checks

---

## 2. MỤC TIÊU SẢN PHẨM

### 2.1 Mục tiêu chính (Must-have)

- [ ] **Multi-provider LLM abstraction layer** — unified interface cho Groq, Gemini, Anthropic
- [ ] **End-to-end RAG pipeline** — từ document upload đến contextualized answer
- [ ] **POST /evaluate** với RAGAS-style metrics (faithfulness, relevancy, context_recall)
- [ ] **POST /compare** — killer feature, so sánh 3 providers song song với `asyncio.gather()`
- [ ] **Collection management API** — CRUD operations trên Qdrant collections
- [ ] **Docker Compose production setup** — 1 lệnh `docker compose up` là chạy được
- [ ] **Auto-generated OpenAPI docs** — FastAPI tự sinh, không cần maintain riêng
- [ ] **Postman collection + sample PDFs** — reviewer test được ngay

### 2.2 Mục tiêu phụ (Should-have)

- [ ] Structured logging với request timing middleware
- [ ] File deduplication (sha256 hash check)
- [ ] Graceful degradation khi 1 provider fail
- [ ] `.env.example` đầy đủ documentation
- [ ] ARCHITECTURE.md với design decisions & tradeoffs

### 2.3 Tính năng nâng cao (Nice-to-have, nếu còn time)

- [ ] Streaming SSE cho POST /ask với `stream=true`
- [ ] Per-request cost tracking (token count × model pricing)
- [ ] DELETE /documents/{doc_id} — xóa document đơn lẻ thay vì cả collection
- [ ] Semantic chunking với SemanticChunker

---

## 3. STAKEHOLDERS & YÊU CẦU

### 3.1 Bảng Stakeholders

| Stakeholder | Vai trò | Nhu cầu cốt lõi | Định nghĩa thành công |
|-------------|---------|-----------------|----------------------|
| **Developer (Tuan)** | Builder | Clean architecture, demonstrable skills | Code reviewer ấn tượng, được gọi phỏng vấn |
| **Edtronaut Tech Lead** | Evaluator | RAG expertise, eval metrics, code quality | Thấy được technical depth và production mindset |
| **End Users (học viên)** | Consumer | Accurate answers từ course content, không hallucinate | Câu trả lời faithful với context, không bịa đặt |

### 3.2 User Stories

**Persona: Học viên muốn ôn thi**
```
AS a student,
I WANT to ask questions about my uploaded course materials
SO THAT I can get accurate answers without reading the entire document.
```

**Persona: Instructor muốn verify AI quality**
```
AS an instructor,
I WANT to evaluate the faithfulness of AI answers against my course content
SO THAT I can trust the system won't mislead students.
```

**Persona: Developer / Tech Lead tại Edtronaut**
```
AS a tech lead,
I WANT to compare multiple LLM providers on the same query
SO THAT I can make data-driven decisions about which provider to use in production.
```

### 3.3 Acceptance Criteria

- **Upload**: File PDF/DOCX/TXT được xử lý thành công, trả về `chunks_created` count
- **Ask**: `provider=groq|gemini|anthropic` đều trả về answer trong < 5 giây
- **Compare**: 3 providers trả về song song trong < 15 giây, side-by-side comparison rõ ràng
- **Evaluate**: `faithfulness` score > 0.80 trên test cases với answer bám sát context
- **Docker**: `docker compose up` từ fresh clone hoạt động không cần manual config

---

## 4. KIẾN TRÚC HỆ THỐNG

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│              (Postman · curl · Frontend App)                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP REST
┌─────────────────────────▼───────────────────────────────────────┐
│                       FastAPI APPLICATION                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │/documents│  │   /ask   │  │ /compare │  │  /evaluate   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│                         │                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    SERVICE LAYER                           │ │
│  │  FileParser  │  Chunker  │  EmbeddingService  │  Router   │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────┬────────────────────────┬────────────────────────────┘
           │                        │
┌──────────▼──────┐      ┌──────────▼──────────────────────────┐
│  Qdrant Vector  │      │           LLM PROVIDERS              │
│    Database     │      │  ┌──────┐  ┌────────┐  ┌─────────┐  │
│  (port 6333)    │      │  │ Groq │  │ Gemini │  │Anthropic│  │
│                 │      │  └──────┘  └────────┘  └─────────┘  │
│  Collections:   │      └─────────────────────────────────────┘
│  - vectors      │
│  - metadata     │
│  - payload      │
└─────────────────┘
```

### 4.2 Ingestion Pipeline (chi tiết)

```
[User Upload]
     │
     ▼
[File Type Detection]
     │
     ├── .pdf  → pypdf2.PdfReader  → extract text per page
     ├── .docx → python-docx       → extract paragraphs
     └── .txt  → plain read        → as-is
     │
     ▼
[SHA256 Hash Deduplication]
     │ hash = sha256(file_content)
     │ if hash in qdrant: return existing doc_id, skip
     │
     ▼
[Text Chunking]
     │ RecursiveCharacterTextSplitter
     │ chunk_size = 512 tokens
     │ chunk_overlap = 50 tokens
     │ separators = ["\n\n", "\n", " "]
     │
     ▼
[Embedding Generation]
     │ model: all-MiniLM-L6-v2 (384-dim)
     │ batch_size = 32 (memory efficient)
     │ normalize_embeddings = True
     │
     ▼
[Qdrant Upsert]
     │ point_id = uuid5(namespace, doc_id + chunk_index)
     │ vector = embedding[384]
     │ payload = {doc_id, source, chunk_index, page, text, collection}
     ▼
[Response]
     {"doc_id": "sha256:...", "chunks_created": 42, "processing_ms": 1240}
```

### 4.3 Query Pipeline (chi tiết)

```
[User Query: "Explain gradient descent"]
     │
     ▼
[Embed Query]
     │ SAME model: all-MiniLM-L6-v2 (CRITICAL!)
     │ output: query_vector[384]
     │
     ▼
[Qdrant Similarity Search]
     │ metric: cosine similarity
     │ top_k = 5 (configurable, default 5)
     │ filter: payload.collection == requested_collection
     │ return: [(chunk_text, score, metadata), ...]
     │
     ▼
[Context Assembly]
     │ Join top-k chunks với separator
     │ Cap total tokens ≤ 4000 (5 chunks × ~800 tokens)
     │ Truncate if overflow
     │
     ▼
[Prompt Construction]
     │ System: "Answer ONLY from the context below. If the answer
     │          is not in the context, say 'I don't know'."
     │ User: f"Context:\n{context}\n\nQuestion: {question}"
     │
     ▼
[LLM Router]
     │ provider = get_provider(requested_provider)
     │ response = await provider.complete(prompt)
     │
     ▼
[Response]
     {"answer": "...", "latency_ms": 524, "chunks_used": 5, ...}
```

### 4.4 Compare Pipeline (Killer Feature)

```
[User: POST /compare {"question": "...", "collection": "..."}]
     │
     ▼
[Context Retrieval] (1 lần, shared cho tất cả providers)
     │ top_k Qdrant search → context chunks
     │
     ▼
[asyncio.gather() — 3 concurrent LLM calls]
     │
     ├── GroqProvider.complete(prompt)      → {answer, latency: 312ms, tokens: 420}
     ├── GeminiProvider.complete(prompt)    → {answer, latency: 890ms, tokens: 380}
     └── AnthropicProvider.complete(prompt) → {answer, latency: 1120ms, tokens: 395}
     │
     [timeout = 15s per provider, individual error handling]
     │
     ▼
[Aggregate & Return side-by-side comparison]
```

---

## 5. TECHNOLOGY STACK

### 5.1 Quyết định công nghệ & Rationale

| Component | Công nghệ chọn | Thay thế đã xem xét | Lý do chọn |
|-----------|---------------|---------------------|------------|
| **Web Framework** | FastAPI | Flask, Django | Async-native, auto OpenAPI docs, type hints, Pydantic integration |
| **Vector Database** | Qdrant | Chroma, Pinecone, Weaviate | Purpose-built, REST API, payload filtering, collection isolation, tốt hơn Chroma về metadata filtering |
| **Embedding Model** | all-MiniLM-L6-v2 (384-dim) | OpenAI ada-002, text-embedding-3 | Local inference → 0 API cost, fully portable, 384-dim nhanh hơn 1536-dim |
| **LLM Provider 1** | Groq (llama-3.3-70b) | OpenAI GPT-4 | Best latency (~500ms), generous free tier, llama model chất lượng cao |
| **LLM Provider 2** | Gemini 1.5 Flash | Gemini Pro, Claude Sonnet | Free tier, multimodal capability, fast inference |
| **LLM Provider 3** | Claude Haiku 3 | GPT-3.5, Mistral | Quality-first, $0.25/1M tokens, tốt nhất về instruction following |
| **Text Splitter** | LangChain RecursiveCharacterTextSplitter | Custom splitter | Battle-tested, configurable separators, không cần viết lại |
| **Containerization** | Docker Compose | Kubernetes, bare metal | Đủ cho demo, 1 command startup, vendor-neutral |
| **Testing** | pytest + pytest-asyncio | unittest | Async support, fixtures, parametrize |

### 5.2 Tại sao KHÔNG dùng LangChain full chain?

LangChain full chain bị tránh có chủ đích. Lý do:
1. **Abstraction leakage**: Full chain ẩn đi logic, reviewer không thấy được skill thực sự
2. **Debug complexity**: Khi có lỗi trong chain, rất khó trace
3. **Overhead**: Chỉ cần TextSplitter và document loaders — phần còn lại tự viết để demonstrate understanding
4. **Portfolio value**: Tự viết LLM routing layer thể hiện senior-level thinking

### 5.3 Python Dependencies

```txt
# Core
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12        # file upload
pydantic-settings==2.6.0        # config từ .env

# AI/ML
sentence-transformers==3.3.1    # all-MiniLM-L6-v2
langchain-text-splitters==0.3.2 # RecursiveCharacterTextSplitter only

# Vector DB
qdrant-client==1.12.1

# LLM Providers
groq==0.13.0
google-generativeai==0.8.3
anthropic==0.40.0

# File Parsing
pypdf2==3.0.1
python-docx==1.1.2

# Evaluation
ragas==0.2.6                    # optional — custom fallback nếu fail
scikit-learn==1.5.2             # cosine_similarity cho custom metrics

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.28.0                   # async test client cho FastAPI

# Dev
python-dotenv==1.0.1
```

---

## 6. API CONTRACT ĐẦY ĐỦ

### 6.1 Base URL & Headers

```
Base URL: http://localhost:8000
Content-Type: application/json (mặc định)
                multipart/form-data (cho /documents/upload)
```

### 6.2 POST /documents/upload

**Mục đích:** Ingest file vào Qdrant collection

**Request:**
```
Content-Type: multipart/form-data

Fields:
  file       : File    — PDF | DOCX | TXT (required)
  collection : string  — e.g. "math-101" (required)
  doc_name   : string  — display name override (optional)
```

**Response 200:**
```json
{
  "doc_id": "sha256:d7f3a1c8e2b4f9a6...",
  "collection": "math-101",
  "source": "gradient_descent_lecture.pdf",
  "chunks_created": 42,
  "processing_ms": 1240,
  "deduplicated": false
}
```

**Response 400 (file type không hỗ trợ):**
```json
{
  "error": "UNSUPPORTED_FILE_TYPE",
  "message": "File type '.pptx' is not supported. Allowed: pdf, docx, txt",
  "status_code": 400
}
```

**Response 409 (duplicate file):**
```json
{
  "error": "DUPLICATE_DOCUMENT",
  "message": "Document already exists with doc_id 'sha256:d7f3a1...'",
  "doc_id": "sha256:d7f3a1c8e2b4f9a6...",
  "status_code": 409
}
```

---

### 6.3 POST /ask

**Mục đích:** RAG query với LLM provider selection

**Request:**
```json
{
  "question": "Explain the intuition behind gradient descent",
  "collection": "math-101",
  "provider": "groq",
  "top_k": 5,
  "stream": false
}
```

**Validation rules:**
- `question`: string, min_length=3, max_length=1000
- `collection`: string, regex `^[a-z0-9_-]{1,64}$`
- `provider`: enum `["groq", "gemini", "anthropic"]`
- `top_k`: int, ge=1, le=20, default=5
- `stream`: bool, default=false

**Response 200:**
```json
{
  "answer": "Gradient descent is an optimization algorithm that...",
  "provider": "groq",
  "model": "llama-3.3-70b-versatile",
  "latency_ms": 524,
  "chunks_used": 5,
  "total_tokens": 1247,
  "context_preview": [
    "Gradient descent minimizes a function by iteratively...",
    "The learning rate α controls the step size..."
  ],
  "collection": "math-101"
}
```

**Response 404 (collection không tồn tại):**
```json
{
  "error": "COLLECTION_NOT_FOUND",
  "message": "Collection 'math-101' does not exist. Upload documents first.",
  "status_code": 404
}
```

**Response 503 (provider lỗi):**
```json
{
  "error": "PROVIDER_UNAVAILABLE",
  "message": "Groq API returned 429: rate limit exceeded",
  "provider": "groq",
  "status_code": 503
}
```

---

### 6.4 POST /compare ← Killer Feature

**Mục đích:** So sánh tất cả 3 providers song song trong 1 request

**Request:**
```json
{
  "question": "What is the difference between supervised and unsupervised learning?",
  "collection": "ml-fundamentals",
  "top_k": 5
}
```

**Response 200:**
```json
{
  "question": "What is the difference between supervised and unsupervised learning?",
  "collection": "ml-fundamentals",
  "context_chunks": 5,
  "results": {
    "groq": {
      "answer": "Supervised learning uses labeled training data...",
      "model": "llama-3.3-70b-versatile",
      "latency_ms": 312,
      "tokens": 420,
      "estimated_cost_usd": 0.0,
      "status": "success"
    },
    "gemini": {
      "answer": "The key distinction lies in whether the training data...",
      "model": "gemini-1.5-flash",
      "latency_ms": 890,
      "tokens": 380,
      "estimated_cost_usd": 0.0,
      "status": "success"
    },
    "anthropic": {
      "answer": "Supervised learning involves training a model on...",
      "model": "claude-haiku-3",
      "latency_ms": 1120,
      "tokens": 395,
      "estimated_cost_usd": 0.0001,
      "status": "success"
    }
  },
  "fastest_provider": "groq",
  "total_elapsed_ms": 1147
}
```

**Lưu ý về error handling:** Nếu 1 provider fail, response vẫn trả về 200 với `"status": "error"` cho provider đó:
```json
"groq": {
  "status": "error",
  "error": "TIMEOUT",
  "message": "Request timed out after 15s",
  "latency_ms": 15000
}
```

---

### 6.5 POST /evaluate

**Mục đích:** RAGAS-style quality metrics cho RAG output

**Request:**
```json
{
  "question": "What is gradient descent?",
  "answer": "Gradient descent is an optimization algorithm...",
  "context": [
    "Gradient descent minimizes a loss function by iteratively...",
    "The learning rate controls how large each step is..."
  ],
  "ground_truth": "Gradient descent is a first-order optimization algorithm..."
}
```

**Validation rules:**
- `question`: required string
- `answer`: required string
- `context`: required list[string], min 1 chunk
- `ground_truth`: optional — nếu cung cấp, enables `context_recall` metric

**Response 200:**
```json
{
  "faithfulness": 0.92,
  "answer_relevancy": 0.87,
  "context_recall": 0.78,
  "overall_score": 0.86,
  "metrics_detail": {
    "faithfulness": {
      "description": "Fraction of answer statements supported by context",
      "method": "NLI decomposition",
      "score": 0.92
    },
    "answer_relevancy": {
      "description": "Cosine similarity between embedded question and answer",
      "method": "cosine(embed(Q), embed(A))",
      "score": 0.87
    },
    "context_recall": {
      "description": "Ground truth sentences covered by retrieved context",
      "method": "sentence overlap ratio",
      "score": 0.78,
      "requires_ground_truth": true
    }
  },
  "evaluation_ms": 340
}
```

**Formula `overall_score`:**
```
overall_score = (faithfulness × 0.4) + (answer_relevancy × 0.4) + (context_recall × 0.2)
             = (0.92 × 0.4) + (0.87 × 0.4) + (0.78 × 0.2)
             = 0.368 + 0.348 + 0.156 = 0.872 ≈ 0.87
```

---

### 6.6 GET /collections

**Response 200:**
```json
{
  "collections": [
    {
      "name": "math-101",
      "document_count": 3,
      "chunk_count": 156,
      "vector_size": 384,
      "created_at": "2024-01-15T10:30:00Z",
      "disk_size_mb": 2.4
    },
    {
      "name": "ml-fundamentals",
      "document_count": 7,
      "chunk_count": 421,
      "vector_size": 384,
      "created_at": "2024-01-14T08:00:00Z",
      "disk_size_mb": 6.1
    }
  ],
  "total_collections": 2,
  "total_chunks": 577
}
```

---

### 6.7 DELETE /collections/{name}

**Response 200:**
```json
{
  "deleted": true,
  "name": "math-101",
  "points_removed": 156,
  "deletion_ms": 43
}
```

**Response 404:**
```json
{
  "error": "COLLECTION_NOT_FOUND",
  "message": "Collection 'math-101' does not exist",
  "status_code": 404
}
```

---

### 6.8 GET /health & GET /readiness

```json
// GET /health — luôn return 200 nếu app đang chạy
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-01-15T12:00:00Z"
}

// GET /readiness — 200 chỉ khi model loaded + qdrant connected
{
  "status": "ready",
  "embedding_model": "loaded",
  "qdrant": "connected",
  "qdrant_url": "http://qdrant:6333"
}
```

### 6.9 Error Envelope (áp dụng cho mọi error)

```json
{
  "error": "COLLECTION_NOT_FOUND",      // machine-readable error code (SCREAMING_SNAKE_CASE)
  "message": "Human-readable description of what went wrong",
  "status_code": 404,
  "request_id": "req_abc123"            // optional, useful for debugging
}
```

**Danh sách error codes:**

| Code | HTTP Status | Mô tả |
|------|-------------|-------|
| `COLLECTION_NOT_FOUND` | 404 | Collection chưa được tạo |
| `DOCUMENT_NOT_FOUND` | 404 | doc_id không tồn tại |
| `UNSUPPORTED_FILE_TYPE` | 400 | File type không hỗ trợ |
| `DUPLICATE_DOCUMENT` | 409 | File đã được upload (dedup) |
| `INVALID_COLLECTION_NAME` | 400 | Regex validation fail |
| `PROVIDER_UNAVAILABLE` | 503 | LLM provider error |
| `EMBEDDING_MODEL_NOT_READY` | 503 | Model chưa load xong |
| `CONTEXT_TOO_LARGE` | 422 | Context vượt token limit |
| `INVALID_PROVIDER` | 400 | Provider không hợp lệ |

---

## 7. KẾ HOẠCH PHÁT TRIỂN THEO PHASE

---

### PHASE 1 — Foundation & File Ingestion (Day 1, ~8h)

**Goal:** `POST /documents/upload` working end-to-end, chunks được tạo và log ra đúng

#### 7.1.1 Khởi tạo project (1.5h)

```bash
# Khởi tạo cấu trúc
mkdir rag-api && cd rag-api
python -m venv .venv && source .venv/bin/activate

# Tạo folder structure
mkdir -p app/{routers,services/llm,models} tests examples

# Git init
git init
echo "*.pyc\n__pycache__\n.env\n.venv\n*.egg-info" > .gitignore
```

**Tasks cụ thể:**
- [ ] Tạo `requirements.txt` đầy đủ
- [ ] Tạo `.env.example` với tất cả required vars
- [ ] Tạo `app/config.py` — Pydantic Settings đọc từ .env
- [ ] Tạo `app/main.py` — FastAPI app khởi tạo cơ bản
- [ ] Setup pytest: `pytest.ini`, `conftest.py`

**`app/config.py`:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_dim: int = 384
    
    # LLM Providers
    groq_api_key: str
    gemini_api_key: str
    anthropic_api_key: str
    
    # RAG Config
    default_chunk_size: int = 512
    default_chunk_overlap: int = 50
    default_top_k: int = 5
    max_context_tokens: int = 4000
    llm_timeout_seconds: int = 15
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 7.1.2 File Parsing Service (2h)

**Tasks:**
- [ ] `app/services/parser.py` — `FileParser` class với 3 extractors
- [ ] `app/services/chunker.py` — `ChunkingService` wrapper
- [ ] Test với sample files (PDF, DOCX, TXT)

```python
# app/services/parser.py
import hashlib
from pathlib import Path
from typing import Optional
import pypdf2
import docx

class FileParser:
    SUPPORTED_TYPES = {".pdf", ".docx", ".txt"}
    
    def parse(self, file_bytes: bytes, filename: str) -> dict:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: {suffix}")
        
        doc_id = "sha256:" + hashlib.sha256(file_bytes).hexdigest()[:16]
        
        if suffix == ".pdf":
            text = self._parse_pdf(file_bytes)
        elif suffix == ".docx":
            text = self._parse_docx(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
        
        return {"doc_id": doc_id, "text": text, "source": filename}
    
    def _parse_pdf(self, data: bytes) -> str:
        import io
        reader = pypdf2.PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    
    def _parse_docx(self, data: bytes) -> str:
        import io
        doc = docx.Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
```

#### 7.1.3 API Layer (2h)

**Tasks:**
- [ ] `app/models/schemas.py` — Pydantic models cho request/response
- [ ] `app/routers/documents.py` — `POST /documents/upload`
- [ ] `GET /health`, `GET /readiness` endpoints

```python
# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UploadResponse(BaseModel):
    doc_id: str
    collection: str
    source: str
    chunks_created: int
    processing_ms: int
    deduplicated: bool = False

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    collection: str = Field(..., pattern=r"^[a-z0-9_-]{1,64}$")
    provider: str = Field(default="groq")
    top_k: int = Field(default=5, ge=1, le=20)
    stream: bool = False

class CompareRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    collection: str = Field(..., pattern=r"^[a-z0-9_-]{1,64}$")
    top_k: int = Field(default=5, ge=1, le=20)

class EvaluateRequest(BaseModel):
    question: str
    answer: str
    context: List[str] = Field(..., min_length=1)
    ground_truth: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
```

#### 7.1.4 Testing Phase 1 (1h)

```bash
# Test parser
pytest tests/test_parser.py -v

# Manual test
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@examples/sample.pdf" \
  -F "collection=test"
```

**Expected output:**
```json
{"doc_id": "sha256:abc123...", "chunks_created": 24, "processing_ms": 340}
```

**End-of-day deliverable:** Upload file → parse → chunk → log chunk count ✓

---

### PHASE 2 — Embedding & Vector Storage (Day 2, ~8h)

**Goal:** Chunks được embed và stored vào Qdrant, có thể verify qua Qdrant dashboard

#### 7.2.1 Embedding Service (2.5h)

**Critical design decision:** Load model **một lần** trên startup, không lazy load.

```python
# app/services/embedder.py
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingService:
    _instance: "EmbeddingService" = None
    _model: SentenceTransformer = None
    _is_loaded: bool = False
    
    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    def load_model(self, model_name: str):
        """Call this ONCE on FastAPI startup event."""
        self._model = SentenceTransformer(model_name)
        self._is_loaded = True
    
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self._is_loaded:
            raise RuntimeError("Embedding model not loaded yet")
        
        embeddings = self._model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings.tolist()
    
    async def embed_query(self, query: str) -> List[float]:
        result = await self.embed_texts([query])
        return result[0]

# app/main.py startup event
from fastapi import FastAPI
from app.services.embedder import EmbeddingService
from app.config import settings

app = FastAPI(title="Multi-LLM RAG API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    embedder = EmbeddingService.get_instance()
    embedder.load_model(settings.embedding_model)
    print(f"✓ Embedding model loaded: {settings.embedding_model}")
```

**Tasks:**
- [ ] `EmbeddingService` singleton class
- [ ] Startup event trong `main.py`
- [ ] Unit test: embed same text → identical vectors (determinism check)
- [ ] GET /readiness check model loaded status

#### 7.2.2 Qdrant Integration (3h)

```python
# app/services/vector_store.py
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)
from typing import List, Tuple, Optional
import uuid

class QdrantService:
    def __init__(self, url: str, vector_size: int = 384):
        self.client = QdrantClient(url=url)
        self.vector_size = vector_size
    
    def ensure_collection(self, collection_name: str):
        """Create collection if not exists."""
        existing = [c.name for c in self.client.get_collections().collections]
        if collection_name not in existing:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
    
    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
        doc_id: str,
        source: str
    ):
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Deterministic UUID từ doc_id + chunk index
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}:{idx}"))
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "doc_id": doc_id,
                    "source": source,
                    "chunk_index": idx,
                    "text": chunk,
                    "collection": collection_name
                }
            ))
        self.client.upsert(collection_name=collection_name, points=points)
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True
        )
        return [(hit.payload["text"], hit.score) for hit in results]
    
    def check_duplicate(self, collection_name: str, doc_id: str) -> bool:
        """Return True nếu doc đã tồn tại."""
        try:
            results = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]),
                limit=1
            )
            return len(results[0]) > 0
        except Exception:
            return False
```

**Tasks:**
- [ ] `QdrantService` với `ensure_collection`, `upsert_chunks`, `search`, `check_duplicate`
- [ ] GET /collections endpoint — list + stats
- [ ] DELETE /collections/{name}
- [ ] Docker Compose với Qdrant service

```yaml
# docker-compose.yml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
    env_file:
      - .env
    depends_on:
      qdrant:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/readyz"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  qdrant_data:
```

#### 7.2.3 Testing Phase 2 (1.5h)

```bash
# Start services
docker compose up qdrant -d

# Run integration test
pytest tests/test_integration.py -v -k "test_upload_and_store"

# Verify via Qdrant dashboard
open http://localhost:6333/dashboard
```

**Verify trên Qdrant UI:**
- Collection `test` tồn tại
- Points count = chunks_created từ API response
- Payload fields đầy đủ: doc_id, source, chunk_index, text

**End-of-day deliverable:** Qdrant dashboard shows correct points với full payload ✓

---

### PHASE 3 — Multi-LLM Orchestration (Day 3, ~8h)

**Goal:** `POST /ask` và `POST /compare` working với cả 3 providers

#### 7.3.1 LLM Provider Abstraction Layer (2.5h)

```python
# app/services/llm/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMResponse:
    answer: str
    model: str
    latency_ms: int
    tokens: int
    estimated_cost_usd: float = 0.0

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        ...
    
    @property
    @abstractmethod
    def name(self) -> str:
        ...
    
    @property
    @abstractmethod
    def model_id(self) -> str:
        ...
```

```python
# app/services/llm/groq.py
import time
from groq import AsyncGroq
from .base import LLMProvider, LLMResponse

class GroqProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
    
    @property
    def name(self): return "groq"
    
    @property
    def model_id(self): return "llama-3.3-70b-versatile"
    
    async def complete(self, prompt: str, system: str = "") -> LLMResponse:
        start = time.monotonic()
        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        usage = response.usage
        
        return LLMResponse(
            answer=response.choices[0].message.content,
            model=self.model_id,
            latency_ms=latency_ms,
            tokens=usage.total_tokens,
            estimated_cost_usd=0.0  # Groq free tier
        )
```

```python
# app/services/llm/factory.py
from app.config import settings
from .groq import GroqProvider
from .gemini import GeminiProvider
from .anthropic import AnthropicProvider
from .base import LLMProvider

_providers: dict[str, LLMProvider] = {}

def get_provider(name: str) -> LLMProvider:
    if not _providers:
        _providers["groq"] = GroqProvider(settings.groq_api_key)
        _providers["gemini"] = GeminiProvider(settings.gemini_api_key)
        _providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key)
    
    if name not in _providers:
        raise ValueError(f"Unknown provider: {name}. Allowed: {list(_providers.keys())}")
    
    return _providers[name]
```

#### 7.3.2 RAG Service & Prompt Engineering (2h)

```python
# app/services/rag.py
from app.services.embedder import EmbeddingService
from app.services.vector_store import QdrantService

RAG_SYSTEM_PROMPT = """You are an educational assistant. 
Your task is to answer questions based ONLY on the provided context.
If the answer is not explicitly in the context, say "I don't have enough information in the provided materials to answer this question."
Do NOT make up information. Do NOT use prior knowledge outside the context."""

class RAGService:
    def __init__(self, embedder: EmbeddingService, vector_store: QdrantService):
        self.embedder = embedder
        self.vector_store = vector_store
    
    async def retrieve_context(
        self, question: str, collection: str, top_k: int = 5
    ) -> list[str]:
        query_vector = await self.embedder.embed_query(question)
        results = self.vector_store.search(collection, query_vector, top_k)
        return [text for text, score in results]
    
    def build_prompt(self, question: str, context_chunks: list[str]) -> str:
        context = "\n\n---\n\n".join(context_chunks)
        return f"""Context from course materials:

{context}

---

Question: {question}

Please answer based ONLY on the context above."""
```

#### 7.3.3 POST /ask & POST /compare Endpoints (2h)

```python
# app/routers/ask.py
import asyncio
import time
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import AskRequest, CompareRequest
from app.services.llm.factory import get_provider
from app.services.rag import RAGService

router = APIRouter()

@router.post("/ask")
async def ask(request: AskRequest, rag: RAGService = Depends(get_rag_service)):
    chunks = await rag.retrieve_context(request.question, request.collection, request.top_k)
    if not chunks:
        raise HTTPException(404, detail={"error": "COLLECTION_NOT_FOUND", ...})
    
    prompt = rag.build_prompt(request.question, chunks)
    provider = get_provider(request.provider)
    
    result = await provider.complete(prompt, system=RAG_SYSTEM_PROMPT)
    
    return {
        "answer": result.answer,
        "provider": provider.name,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "chunks_used": len(chunks),
        "context_preview": [c[:200] + "..." for c in chunks[:2]]
    }

@router.post("/compare")
async def compare(request: CompareRequest, rag: RAGService = Depends(get_rag_service)):
    chunks = await rag.retrieve_context(request.question, request.collection, request.top_k)
    prompt = rag.build_prompt(request.question, chunks)
    
    start = time.monotonic()
    
    async def call_provider(name: str):
        try:
            provider = get_provider(name)
            result = await asyncio.wait_for(
                provider.complete(prompt, system=RAG_SYSTEM_PROMPT),
                timeout=15.0
            )
            return name, {"answer": result.answer, "latency_ms": result.latency_ms,
                         "tokens": result.tokens, "status": "success"}
        except asyncio.TimeoutError:
            return name, {"status": "error", "error": "TIMEOUT", "latency_ms": 15000}
        except Exception as e:
            return name, {"status": "error", "error": str(e)}
    
    tasks = [call_provider(p) for p in ["groq", "gemini", "anthropic"]]
    raw_results = await asyncio.gather(*tasks)
    results = dict(raw_results)
    
    total_ms = int((time.monotonic() - start) * 1000)
    fastest = min(
        (p for p in results if results[p]["status"] == "success"),
        key=lambda p: results[p]["latency_ms"],
        default=None
    )
    
    return {
        "question": request.question,
        "results": results,
        "fastest_provider": fastest,
        "total_elapsed_ms": total_ms
    }
```

#### 7.3.4 Testing Phase 3 (1.5h)

```bash
# Test all providers
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is gradient descent?", "collection": "math-101", "provider": "groq"}'

curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is gradient descent?", "collection": "math-101"}'
```

**End-of-day deliverable:** `POST /ask` với cả 3 providers trả về meaningful answers ✓

---

### PHASE 4 — Evaluation Engine (Day 4, ~8h)

**Goal:** `POST /evaluate` trả về RAGAS-style quality metrics đáng tin cậy

#### 7.4.1 Custom Metrics Implementation (3h)

> **Strategy:** Implement custom metrics trước, RAGAS là optional enhancement.
> Custom metrics đủ tốt cho demo và không có dependency issues.

```python
# app/services/evaluator.py
from typing import List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.services.embedder import EmbeddingService

class RAGEvaluator:
    def __init__(self, embedder: EmbeddingService):
        self.embedder = embedder
    
    async def evaluate(
        self,
        question: str,
        answer: str,
        context: List[str],
        ground_truth: Optional[str] = None
    ) -> dict:
        results = {}
        
        # Metric 1: Faithfulness
        results["faithfulness"] = await self._faithfulness(answer, context)
        
        # Metric 2: Answer Relevancy
        results["answer_relevancy"] = await self._answer_relevancy(question, answer)
        
        # Metric 3: Context Recall (requires ground_truth)
        if ground_truth:
            results["context_recall"] = await self._context_recall(context, ground_truth)
            weights = {"faithfulness": 0.4, "answer_relevancy": 0.4, "context_recall": 0.2}
        else:
            results["context_recall"] = None
            weights = {"faithfulness": 0.5, "answer_relevancy": 0.5}
        
        # Overall score
        results["overall_score"] = sum(
            results[k] * w for k, w in weights.items() if results.get(k) is not None
        )
        
        return results
    
    async def _faithfulness(self, answer: str, context: List[str]) -> float:
        """
        Faithfulness = fraction of answer sentences that are semantically
        similar to at least one context chunk.
        Method: cosine similarity between embedded sentences.
        """
        answer_sentences = [s.strip() for s in answer.split('.') if len(s.strip()) > 20]
        if not answer_sentences:
            return 1.0
        
        full_context = " ".join(context)
        
        # Embed answer sentences and full context
        texts_to_embed = answer_sentences + [full_context]
        embeddings = await self.embedder.embed_texts(texts_to_embed)
        
        sentence_embeds = np.array(embeddings[:-1])
        context_embed = np.array(embeddings[-1:])
        
        similarities = cosine_similarity(sentence_embeds, context_embed).flatten()
        
        # Fraction of sentences with similarity > 0.7 threshold
        supported = np.sum(similarities > 0.7)
        return float(supported / len(answer_sentences))
    
    async def _answer_relevancy(self, question: str, answer: str) -> float:
        """
        Answer Relevancy = cosine similarity between embedded question and answer.
        """
        embeddings = await self.embedder.embed_texts([question, answer])
        q_embed = np.array(embeddings[0:1])
        a_embed = np.array(embeddings[1:2])
        return float(cosine_similarity(q_embed, a_embed)[0][0])
    
    async def _context_recall(self, context: List[str], ground_truth: str) -> float:
        """
        Context Recall = fraction of ground truth sentences covered by context.
        """
        gt_sentences = [s.strip() for s in ground_truth.split('.') if len(s.strip()) > 10]
        if not gt_sentences:
            return 1.0
        
        full_context = " ".join(context)
        texts = gt_sentences + [full_context]
        embeddings = await self.embedder.embed_texts(texts)
        
        gt_embeds = np.array(embeddings[:-1])
        ctx_embed = np.array(embeddings[-1:])
        
        similarities = cosine_similarity(gt_embeds, ctx_embed).flatten()
        covered = np.sum(similarities > 0.65)
        return float(covered / len(gt_sentences))
```

#### 7.4.2 RAGAS Integration (Optional, 1.5h)

```python
# app/services/ragas_evaluator.py (optional enhancement)
# Chỉ dùng nếu custom metrics chưa đủ

try:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_recall
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False

async def evaluate_with_ragas(question, answer, contexts, ground_truth=None):
    if not RAGAS_AVAILABLE:
        return None  # Fallback to custom metrics
    
    # ... RAGAS evaluation logic
```

#### 7.4.3 Global Error Handling & Middleware (2h)

```python
# app/main.py — global error handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": str(exc),
            "status_code": 500
        }
    )

# Logging middleware
import time
import logging

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    
    logging.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} [{elapsed_ms}ms]"
    )
    
    response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
    return response
```

#### 7.4.4 Testing Phase 4 (1.5h)

```bash
# Test evaluation endpoint
curl -X POST "http://localhost:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is gradient descent?",
    "answer": "Gradient descent is an optimization algorithm that minimizes a function by iteratively moving in the direction of steepest descent.",
    "context": ["Gradient descent minimizes a loss function by iteratively moving in the steepest descent direction."],
    "ground_truth": "Gradient descent is a first-order optimization algorithm."
  }'
```

**Expected:** `faithfulness > 0.80`, `answer_relevancy > 0.85`

**End-of-day deliverable:** POST /evaluate returns faithfulness > 0.8 trên 3 test cases ✓

---

### PHASE 5 — Production Hardening & Documentation (Day 5, ~8h)

**Goal:** Production-ready Docker Compose + comprehensive README + polished demo

#### 7.5.1 Multi-stage Dockerfile (1.5h)

```dockerfile
# Dockerfile
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY examples/ ./examples/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 7.5.2 Integration Tests (2h)

```python
# tests/test_integration.py
import pytest
import httpx

@pytest.fixture
async def client():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as c:
        yield c

@pytest.mark.asyncio
async def test_full_rag_flow(client):
    """Upload → Ask → Evaluate full flow."""
    
    # 1. Upload sample PDF
    with open("examples/sample_ml.pdf", "rb") as f:
        response = await client.post("/documents/upload", files={
            "file": ("sample_ml.pdf", f, "application/pdf")
        }, data={"collection": "test-integration"})
    
    assert response.status_code == 200
    upload_data = response.json()
    assert upload_data["chunks_created"] > 0
    
    # 2. Ask question
    ask_response = await client.post("/ask", json={
        "question": "What is machine learning?",
        "collection": "test-integration",
        "provider": "groq"
    })
    assert ask_response.status_code == 200
    ask_data = ask_response.json()
    assert len(ask_data["answer"]) > 50
    
    # 3. Evaluate
    eval_response = await client.post("/evaluate", json={
        "question": "What is machine learning?",
        "answer": ask_data["answer"],
        "context": ask_data["context_preview"]
    })
    assert eval_response.status_code == 200
    eval_data = eval_response.json()
    assert eval_data["faithfulness"] > 0.6
    assert eval_data["answer_relevancy"] > 0.7

@pytest.mark.asyncio
async def test_compare_endpoint(client):
    """All 3 providers return responses."""
    response = await client.post("/compare", json={
        "question": "What is machine learning?",
        "collection": "test-integration"
    })
    assert response.status_code == 200
    data = response.json()
    assert "groq" in data["results"]
    assert "gemini" in data["results"]
    assert "anthropic" in data["results"]
    assert data["fastest_provider"] is not None
```

#### 7.5.3 Sample Files & Demo Setup (1h)

Tạo ít nhất 3 sample PDFs trong `/examples`:
- `intro_to_ml.pdf` — Introduction to Machine Learning (5-10 trang)
- `deep_learning_basics.pdf` — Deep Learning fundamentals
- `nlp_fundamentals.pdf` — Natural Language Processing intro

Nếu không có sẵn PDF, dùng script để generate:
```python
# scripts/generate_sample_pdfs.py
from reportlab.pdfgen import canvas
# Tạo PDFs từ Wikipedia content về ML topics
```

#### 7.5.4 README & Documentation (2h)

README phải bao gồm:
1. **Architecture diagram** (ASCII art hoặc Mermaid) — reviewer đọc đây đầu tiên
2. **5-minute quickstart** — từ `git clone` đến working demo
3. **API reference** với cURL examples cho mọi endpoint
4. **Design decisions** — tại sao chọn Qdrant thay vì Chroma, etc.
5. **Evaluation methodology** — giải thích faithfulness, relevancy metrics

```markdown
## Quickstart

\`\`\`bash
# 1. Clone & setup
git clone https://github.com/yourusername/rag-api
cd rag-api
cp .env.example .env
# Edit .env với API keys của bạn

# 2. Start services
docker compose up -d

# 3. Wait for readiness
curl http://localhost:8000/readiness

# 4. Upload sample document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@examples/intro_to_ml.pdf" \
  -F "collection=demo"

# 5. Ask a question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is supervised learning?", "collection": "demo", "provider": "groq"}'

# 6. Compare all providers
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is supervised learning?", "collection": "demo"}'
\`\`\`
```

**End-of-day deliverable:** `docker compose up` từ fresh clone → fully working ✓

---

## 8. CẤU TRÚC THƯ MỤC DỰ ÁN

```
rag-api/
├── app/
│   ├── main.py                  # FastAPI app, startup events (preload model here)
│   ├── config.py                # Settings từ .env (EMBEDDING_MODEL, provider keys)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── documents.py         # POST /documents/upload, GET /collections
│   │   ├── ask.py               # POST /ask, POST /compare
│   │   └── evaluate.py          # POST /evaluate
│   ├── services/
│   │   ├── __init__.py
│   │   ├── parser.py            # FileParser: PDF/DOCX/TXT → plain text
│   │   ├── chunker.py           # RecursiveCharacterTextSplitter wrapper
│   │   ├── embedder.py          # EmbeddingService singleton (loaded on startup)
│   │   ├── vector_store.py      # QdrantService: upsert, search, delete
│   │   ├── rag.py               # RAGService: context retrieval + prompt building
│   │   ├── evaluator.py         # Custom RAGAS-style metrics
│   │   ├── ragas_evaluator.py   # Optional: real RAGAS integration
│   │   └── llm/
│   │       ├── __init__.py
│   │       ├── base.py          # LLMProvider ABC + LLMResponse dataclass
│   │       ├── factory.py       # get_provider(name) factory function
│   │       ├── groq.py          # GroqProvider
│   │       ├── gemini.py        # GeminiProvider
│   │       └── anthropic.py     # AnthropicProvider
│   └── models/
│       ├── __init__.py
│       └── schemas.py           # Tất cả Pydantic request/response models
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures: test client, mock providers
│   ├── test_parser.py           # Unit tests: FileParser
│   ├── test_embedder.py         # Unit tests: EmbeddingService
│   ├── test_vector_store.py     # Unit tests: QdrantService (mocked)
│   ├── test_evaluator.py        # Unit tests: RAGEvaluator metrics
│   └── test_integration.py      # E2E: upload → ask → evaluate flow
│
├── examples/                    # Sample PDFs cho reviewer test ngay
│   ├── intro_to_ml.pdf
│   ├── deep_learning_basics.pdf
│   └── nlp_fundamentals.pdf
│
├── scripts/
│   ├── generate_sample_pdfs.py  # Generate sample PDFs nếu cần
│   └── seed_demo_data.py        # Pre-upload examples và seed demo collections
│
├── docker-compose.yml           # API + Qdrant services
├── Dockerfile                   # Multi-stage: builder + runtime
├── .env.example                 # Template với tất cả required vars
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Dev/test dependencies
├── pytest.ini                   # pytest configuration
├── ARCHITECTURE.md              # Design decisions + tradeoffs + diagrams
└── README.md                    # 5-min quickstart + API docs + examples
```

---

## 9. SCHEMA & DATA MODELS

### 9.1 Qdrant Point Schema

| Field | Type | Mô tả |
|-------|------|-------|
| `id` | UUID | Deterministic UUID5 từ `doc_id:chunk_index` — đảm bảo idempotent upsert |
| `vector` | float[384] | all-MiniLM-L6-v2 embedding, L2-normalized |
| `payload.doc_id` | string | `sha256:` prefix + 16-char hex của file content hash |
| `payload.source` | string | Original filename (`lecture_01.pdf`) |
| `payload.chunk_index` | int | Position trong document (0-based), dùng cho ordering |
| `payload.page` | int? | Page number (PDF only, null cho DOCX/TXT) |
| `payload.text` | string | Raw chunk text — cần thiết để inject vào prompt |
| `payload.collection` | string | Logical collection name — cho cross-collection filtering |

### 9.2 .env Configuration

```bash
# .env.example

# Embedding (DO NOT CHANGE after first upload — mismatch sẽ break cosine similarity)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Qdrant
QDRANT_URL=http://qdrant:6333

# LLM Provider API Keys
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...

# RAG Configuration
DEFAULT_CHUNK_SIZE=512
DEFAULT_CHUNK_OVERLAP=50
DEFAULT_TOP_K=5
MAX_CONTEXT_TOKENS=4000
LLM_TIMEOUT_SECONDS=15
```

### 9.3 Collection Naming Rules

```
Regex: ^[a-z0-9_-]{1,64}$

Valid:   math-101, ml_fundamentals, course2024
Invalid: Math101 (uppercase), course/1 (slash), a (too short if len<2)
```

---

## 10. RISK MANAGEMENT

### 10.1 Risk Matrix

| Risk | Impact | Likelihood | Mitigation Strategy |
|------|--------|------------|---------------------|
| **Embedding model cold start delay** | High | High | Preload trên startup event. GET /readiness blocked cho đến khi model loaded. K8s readinessProbe nếu production. |
| **LLM API rate limits** | High | Medium | Exponential backoff retry (3x, 1s/2s/4s). Provider fallback chain: Groq → Gemini → Anthropic. Log rate limit headers. |
| **Context window overflow** | High | Medium | Cap total context tại 4000 tokens (5 chunks × ~800 tokens). Truncate từ cuối nếu vượt. Log khi truncate. |
| **RAGAS installation complexity** | Medium | High | Custom metrics là primary path. RAGAS là optional enhancement. Note clearly trong README. |
| **Embedding model mismatch (ingest vs query)** | Critical | Low | Single EMBEDDING_MODEL config var. Enforce tại EmbeddingService layer. Integration test: assert embed consistency. |
| **Qdrant collection name conflict** | Low | Medium | Validate regex `^[a-z0-9_-]{1,64}$` tại Pydantic model. Check existence trước khi create. |
| **asyncio.gather() partial failures** | Medium | Medium | Individual try/except cho mỗi provider. Return `status: "error"` thay vì fail toàn bộ request. |
| **Large file upload (>50MB)** | Medium | Low | Set max file size = 20MB tại FastAPI. Validate sớm trước khi parse. |

### 10.2 Contingency Plans

**Nếu RAGAS quá complex (Day 4):**
→ Ship với custom metrics (faithfulness + relevancy). Note trong README: "RAGAS integration available — run `pip install ragas` to enable enhanced metrics." Thêm vào backlog.

**Nếu 1 LLM provider không có API key khi demo:**
→ `/compare` vẫn return 200 với `status: "error"` cho provider đó. Demo vẫn work với 2/3 providers.

**Nếu Qdrant container crash:**
→ Data vẫn persist nhờ `qdrant_data` Docker volume. `docker compose restart qdrant` là đủ.

---

## 11. KPIs & ĐỊNH NGHĨA THÀNH CÔNG

### 11.1 Functional KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| All 3 providers respond correctly | 100% | Manual test POST /compare với 5 queries |
| Upload → ask latency (Groq) | < 3 giây | Time từ curl send đến response |
| Faithfulness score trên test cases | > 0.80 | POST /evaluate với 5 grounded answers |
| /compare returns 3 results parallel | < 15 giây | asyncio.gather() total time |
| File deduplication | 0 duplicate points | Upload cùng file 2 lần, check Qdrant count |

### 11.2 Code Quality KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| Test coverage | > 70% | `pytest --cov=app` |
| Docker cold start time | < 60 giây | `time docker compose up` từ image pull |
| OpenAPI docs completeness | 100% endpoints | Check /docs page |
| Error response consistency | 100% envelope format | Review tất cả error responses |
| No hardcoded secrets | 0 secrets in code | `git grep -i "api_key\|secret"` trả về rỗng |

### 11.3 Portfolio Impact KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| README 5-min quickstart | Anyone can run | Test với fresh machine, fresh clone |
| Architecture diagram | Trong README | Visual reviewer thấy ngay |
| /compare demo output quality | Clear side-by-side | Screenshot trong README |
| Sample PDFs trong /examples | ≥ 3 files | ls examples/*.pdf |
| ARCHITECTURE.md | Design decisions documented | File tồn tại, > 500 words |

---

## 12. ROADMAP TƯƠNG LAI

### Phase 6 — Streaming (1-2 ngày nếu có time)

```
Feature: POST /ask với stream=true
Implementation:
  - async generator từ LLM provider
  - FastAPI StreamingResponse
  - SSE format: "data: {token}\n\n"
  - Frontend: EventSource API

Example response stream:
  data: {"token": "Gradient"}
  data: {"token": " descent"}
  data: {"token": " is"}
  data: {"done": true, "latency_ms": 312}
```

### Phase 7 — Cost Tracking (0.5 ngày)

```
Feature: Per-request cost tracking

Model pricing (June 2024):
  - Groq llama-3.3-70b: Free tier ($0.00)
  - Gemini 1.5 Flash:   Free tier ($0.00)
  - Claude Haiku 3:     $0.25/1M input, $1.25/1M output

Implementation:
  - tokens_in × price_in + tokens_out × price_out
  - Return trong mọi LLM response
  - Aggregate trong /compare
```

### Phase 8 — Document-level Operations (1 ngày)

```
Feature: DELETE /documents/{doc_id}

Implementation:
  - Filter Qdrant points by payload.doc_id
  - qdrant_client.delete() với FilterSelector
  - Return: points_removed count
```

### Phase 9 — Semantic Chunking (1 ngày)

```
Feature: Semantic chunking thay vì character-based

Current:  RecursiveCharacterTextSplitter (512 chars)
Improved: SemanticChunker (LangChain) — chunk theo meaning

Benefits:
  - Chunk boundaries tại logical breaks, không mid-sentence
  - Better retrieval quality (+10-15% faithfulness expected)
  - Slightly slower ingestion (trade-off)

Measurement: A/B test faithfulness score với same documents
```

### Phase 10 — Production Hardening

```
Security:
  - API key authentication (X-API-Key header)
  - Rate limiting per API key
  - Request size limits

Observability:
  - Structured JSON logging (structlog)
  - Prometheus metrics endpoint /metrics
  - Grafana dashboard template

Scalability:
  - Async embedding với batching queue
  - Redis cache cho frequent queries
  - Horizontal scaling: multiple API containers + shared Qdrant
```

---

## 13. HƯỚNG DẪN TRIỂN KHAI

### 13.1 Prerequisites

```bash
# Required
Docker Desktop (hoặc Docker Engine + Docker Compose)
Git

# API Keys cần có
Groq API Key    → https://console.groq.com (free)
Gemini API Key  → https://aistudio.google.com (free)
Anthropic API Key → https://console.anthropic.com ($5 min credit)
```

### 13.2 Setup từ đầu (fresh machine)

```bash
# 1. Clone project
git clone https://github.com/yourusername/rag-api
cd rag-api

# 2. Cấu hình environment
cp .env.example .env
# Mở .env, điền 3 API keys

# 3. Build và start
docker compose up --build -d

# 4. Verify services healthy
docker compose ps
curl http://localhost:8000/readiness
# Expected: {"status": "ready", "embedding_model": "loaded", "qdrant": "connected"}

# 5. Seed demo data
docker compose exec api python scripts/seed_demo_data.py
# Uploads 3 sample PDFs vào collections: ml-basics, dl-intro, nlp-basics

# 6. Test /compare
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is supervised learning?", "collection": "ml-basics"}'
```

### 13.3 Development Setup (local)

```bash
# 1. Python environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# 2. Start only Qdrant via Docker
docker compose up qdrant -d

# 3. Run API locally (hot-reload)
QDRANT_URL=http://localhost:6333 uvicorn app.main:app --reload --port 8000

# 4. Run tests
pytest tests/ -v --cov=app --cov-report=term-missing
```

### 13.4 Demo Script (cho interview / presentation)

```bash
# Step 1: Show clean startup
docker compose down -v          # Start từ scratch
docker compose up -d            # Fresh start
watch -n1 "curl -s http://localhost:8000/readiness | python -m json.tool"

# Step 2: Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@examples/intro_to_ml.pdf" \
  -F "collection=demo" | python -m json.tool

# Step 3: Single provider query
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain the bias-variance tradeoff", "collection": "demo", "provider": "groq"}' \
  | python -m json.tool

# Step 4: THE KILLER FEATURE — compare all 3 providers
curl -X POST "http://localhost:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain the bias-variance tradeoff", "collection": "demo"}' \
  | python -m json.tool

# Step 5: Evaluate quality
curl -X POST "http://localhost:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the bias-variance tradeoff",
    "answer": "The bias-variance tradeoff describes the tension between...",
    "context": ["High bias models underfit the data...", "High variance models overfit..."],
    "ground_truth": "The bias-variance tradeoff is a fundamental problem in supervised learning..."
  }' | python -m json.tool

# Step 6: Show OpenAPI docs
open http://localhost:8000/docs
```

---

## PHỤ LỤC A — Prompt Templates

### RAG System Prompt (production)
```
You are an educational assistant for course content Q&A.

RULES:
1. Answer ONLY based on the provided context below
2. If the answer is not in the context, say exactly: "I don't have enough information in the provided course materials to answer this question."
3. Do NOT use prior knowledge or make assumptions
4. Quote relevant sections when helpful
5. Be concise but complete

These rules ensure students receive accurate information grounded in their course materials.
```

### Context Injection Format
```
=== COURSE MATERIALS CONTEXT ===

[Chunk 1 of 5]
{chunk_1_text}

[Chunk 2 of 5]
{chunk_2_text}

... (additional chunks)

=== END OF CONTEXT ===

Student Question: {question}

Please answer based solely on the context above.
```

---

## PHỤ LỤC B — Postman Collection Structure

```json
{
  "info": { "name": "Multi-LLM RAG API", "schema": "..." },
  "variable": [
    { "key": "base_url", "value": "http://localhost:8000" },
    { "key": "collection", "value": "demo" }
  ],
  "item": [
    {
      "name": "Health & Readiness",
      "item": ["GET /health", "GET /readiness"]
    },
    {
      "name": "Documents",
      "item": ["POST /documents/upload (PDF)", "GET /collections", "DELETE /collections/{name}"]
    },
    {
      "name": "RAG Queries",
      "item": ["POST /ask (Groq)", "POST /ask (Gemini)", "POST /ask (Anthropic)"]
    },
    {
      "name": "🌟 Killer Feature",
      "item": ["POST /compare (all providers)"]
    },
    {
      "name": "Evaluation",
      "item": ["POST /evaluate (with ground_truth)", "POST /evaluate (without ground_truth)"]
    }
  ]
}
```

---

*Kế hoạch này được thiết kế để build trong 5 ngày (40 giờ) với một developer. Mỗi phase có deliverable rõ ràng, có thể verify được. Phase 1-3 là core RAG pipeline; Phase 4-5 là các yếu tố tạo ra sự khác biệt trong mắt Edtronaut interviewer.*

*Phiên bản: 1.0 | Cập nhật: 2024*
