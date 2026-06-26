// Types generated from BE Pydantic schemas (app/models/schemas.py)

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
}

export interface ReadinessResponse {
  status: string
  embedding_model: string
  qdrant: string
  qdrant_url: string
}

export interface UploadResponse {
  doc_id: string
  collection: string
  source: string
  chunks_created: number
  processing_ms: number
  deduplicated: boolean
}

export interface CollectionInfo {
  name: string
  document_count: number
  chunk_count: number
  vector_size: number
  created_at?: string | null
  disk_size_mb?: number | null
}

export interface CollectionsListResponse {
  collections: CollectionInfo[]
  total_collections: number
  total_chunks: number
}

export interface DeleteCollectionResponse {
  deleted: boolean
  name: string
  points_removed: number
  deletion_ms: number
}

export type Provider = 'groq' | 'gemini' | 'anthropic'

export interface AskRequest {
  question: string
  collection: string
  provider?: Provider
  top_k?: number
  stream?: boolean
}

export interface AskResponse {
  answer: string
  provider: string
  model: string
  latency_ms: number
  chunks_used: number
  total_tokens: number
  context_preview: string[]
  collection: string
}

export interface CompareRequest {
  question: string
  collection: string
  top_k?: number
}

export interface CompareProviderResult {
  answer?: string
  model?: string
  latency_ms?: number
  tokens?: number
  estimated_cost_usd?: number
  status: 'success' | 'error'
  error?: string
  message?: string
}

export interface CompareResponse {
  question: string
  collection: string
  context_chunks: number
  results: Record<Provider, CompareProviderResult>
  fastest_provider: Provider | null
  total_elapsed_ms: number
}

export interface EvaluateRequest {
  question: string
  answer: string
  context: string[]
  ground_truth?: string | null
}

export interface MetricDetail {
  description: string
  method: string
  score: number
  requires_ground_truth?: boolean
}

export interface EvaluateResponse {
  faithfulness: number
  answer_relevancy: number
  context_recall: number | null
  overall_score: number
  metrics_detail: Record<string, MetricDetail>
  evaluation_ms: number
}

export interface ApiError {
  error: string
  message: string
  status_code: number
  request_id?: string
  details?: unknown
}
