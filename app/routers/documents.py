"""Document ingestion endpoints."""
from __future__ import annotations

import logging
import re
import time

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.deps import get_chunker, get_embedder, get_parser, get_vector_store
from app.errors import RAGAPIException
from app.services.chunker import ChunkingService
from app.services.embedder import EmbeddingService, ModelNotLoadedError
from app.services.parser import FileParser, UnsupportedFileTypeError
from app.services.vector_store import QdrantService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

_COLLECTION_RE = re.compile(r"^[a-z0-9_-]{1,64}$")


def _validate_collection(name: str) -> None:
    if not _COLLECTION_RE.match(name):
        raise RAGAPIException(
            code="INVALID_COLLECTION_NAME",
            message=(
                "Collection name must match '^[a-z0-9_-]{1,64}$' "
                "(lowercase letters, digits, underscore, hyphen; max 64 chars)."
            ),
            status_code=400,
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(...),
    doc_name: str | None = Form(None),
    parser: FileParser = Depends(get_parser),
    chunker: ChunkingService = Depends(get_chunker),
    embedder: EmbeddingService = Depends(get_embedder),
    vector_store: QdrantService = Depends(get_vector_store),
):
    _validate_collection(collection)
    source = doc_name or file.filename or "uploaded_file"

    raw = await file.read()
    if len(raw) > settings.max_upload_size_mb * 1024 * 1024:
        raise RAGAPIException(
            code="FILE_TOO_LARGE",
            message=f"File exceeds the {settings.max_upload_size_mb}MB upload limit.",
            status_code=413,
        )

    start = time.monotonic()
    try:
        parsed = parser.parse(raw, source)
    except UnsupportedFileTypeError as exc:
        raise RAGAPIException(
            code="UNSUPPORTED_FILE_TYPE", message=str(exc), status_code=400
        )

    chunks = chunker.chunk(parsed["text"])

    try:
        embeddings = await embedder.embed_texts(chunks)
    except ModelNotLoadedError:
        raise RAGAPIException(
            code="EMBEDDING_MODEL_NOT_READY",
            message="Embedding model is not loaded yet. Try again shortly.",
            status_code=503,
        )

    vector_store.ensure_collection(collection)

    if vector_store.check_duplicate(collection, parsed["doc_id"]):
        raise RAGAPIException(
            code="DUPLICATE_DOCUMENT",
            message=f"Document already exists with doc_id '{parsed['doc_id']}'",
            status_code=409,
        )

    created = vector_store.upsert_chunks(
        collection_name=collection,
        chunks=chunks,
        embeddings=embeddings,
        doc_id=parsed["doc_id"],
        source=source,
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        "stored document %s -> %d chunks (%dms)",
        parsed["doc_id"],
        created,
        elapsed_ms,
    )

    return {
        "doc_id": parsed["doc_id"],
        "collection": collection,
        "source": source,
        "chunks_created": created,
        "processing_ms": elapsed_ms,
        "deduplicated": False,
    }
