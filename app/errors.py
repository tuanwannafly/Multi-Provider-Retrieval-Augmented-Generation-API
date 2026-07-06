"""Unified error envelope (see API contract section 6.9)."""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RAGAPIException(Exception):
    """Domain exception that serializes to the standard error envelope."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {"error": self.code, "message": self.message, "status_code": self.status_code}


def rag_error(code: str, message: str, status_code: int) -> RAGAPIException:
    return RAGAPIException(code, message, status_code)


def _request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"


async def rag_exception_handler(request: Request, exc: RAGAPIException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={**exc.to_dict(), "request_id": _request_id(request)},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "INVALID_REQUEST",
            "message": "Request validation failed",
            "status_code": 422,
            "request_id": _request_id(request),
            "details": exc.errors(),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected internal error occurred", # Changed from str(exc)
            "status_code": 500,
            "request_id": _request_id(request),
        },
    )
