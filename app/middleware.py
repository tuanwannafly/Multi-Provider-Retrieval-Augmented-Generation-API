"""HTTP logging + request-timing middleware."""
from __future__ import annotations

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.exception(
                "%s %s -> 500 [%dms]", request.method, request.url.path, elapsed_ms
            )
            raise
        elapsed_ms = int((time.monotonic() - start) * 1000)
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        logger.info(
            "%s %s -> %s [%dms]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
