"""Document ingestion endpoints."""
from __future__ import annotations

import logging
import re
import time

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.deps import get_chunker, get_parser
from app.errors import RAGAPIException
from app.services.chunker import ChunkingService
from app.services.parser import FileParser, UnsupportedFileTypeError

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
    elapsed_ms = int((time.monotonic() - start) * 1000)

    logger.info(
        "parsed document %s -> %d chunks (%dms)",
        parsed["doc_id"],
        len(chunks),
        elapsed_ms,
    )

    return {
        "doc_id": parsed["doc_id"],
        "collection": collection,
        "source": source,
        "chunks_created": len(chunks),
        "processing_ms": elapsed_ms,
        "deduplicated": False,
    }
