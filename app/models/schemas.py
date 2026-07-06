from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


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


class AskResponse(BaseModel):
    answer: str
    provider: str
    model: str
    latency_ms: int
    chunks_used: int
    total_tokens: int
    context_preview: List[str]
    collection: str


class CompareRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    collection: str = Field(..., pattern=r"^[a-z0-9_-]{1,64}$")
    top_k: int = Field(default=5, ge=1, le=20)


class CompareResult(BaseModel):
    answer: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    status: str
    error: Optional[str] = None
    message: Optional[str] = None


class CompareResponse(BaseModel):
    question: str
    collection: str
    context_chunks: int
    results: Dict[str, CompareResult]
    fastest_provider: Optional[str] = None
    total_elapsed_ms: int


class EvaluateRequest(BaseModel):
    question: str
    answer: str
    context: List[str] = Field(..., min_length=1)
    ground_truth: Optional[str] = None


class EvaluateResponse(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_recall: Optional[float]
    overall_score: float
    metrics_detail: dict
    evaluation_ms: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int


class CollectionInfo(BaseModel):
    name: str
    document_count: int
    chunk_count: int
    vector_size: int
    created_at: Optional[str] = None
    disk_size_mb: Optional[float] = None


class CollectionsListResponse(BaseModel):
    collections: List[CollectionInfo]
    total_collections: int
    total_chunks: int


class DeleteCollectionResponse(BaseModel):
    deleted: bool
    name: str
    points_removed: int
    deletion_ms: int


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    status: str
    embedding_model: str
    qdrant: str
    qdrant_url: str
