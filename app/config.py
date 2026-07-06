from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Embedding (DO NOT CHANGE after first upload — mismatch breaks cosine similarity)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_dim: int = 384

    # LLM Providers (defaults to empty string so the module imports without a .env)
    groq_api_key: str = ""
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    # API Key for authentication (optional)
    rag_api_key: str = ""

    # Rate Limiting
    rate_limit_ask: str = "5/minute" # e.g., "5/minute", "100/hour"
    rate_limit_compare: str = "2/minute" # e.g., "2/minute", "50/hour"

    # CORS
    cors_origins: str = "http://localhost:3000" # Comma-separated URLs or "*"

    # RAG configuration
    default_chunk_size: int = 512
    default_chunk_overlap: int = 50
    default_top_k: int = 5
    max_context_tokens: int = 4000
    llm_timeout_seconds: int = 15

    # Upload limits
    max_upload_size_mb: int = 20

    # Application
    app_version: str = "1.0.0"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()