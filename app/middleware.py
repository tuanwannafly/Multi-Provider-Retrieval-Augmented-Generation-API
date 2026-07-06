"""HTTP logging + request-timing middleware."""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        
        # Generate or retrieve request ID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id  # Store on request state

        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.exception(
                "%s %s -> 500 [%dms] (request_id: %s)", 
                request.method, 
                request.url.path, 
                elapsed_ms, 
                request_id # Include request_id in logs
            )
            raise
        
        elapsed_ms = int((time.monotonic() - start) * 1000)
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        response.headers["X-Request-ID"] = request_id # Echo request_id in response headers
        
        logger.info(
            "%s %s -> %s [%dms] (request_id: %s)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id # Include request_id in logs
        )
        return response