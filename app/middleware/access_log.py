"""Lightweight access-log middleware.

Logs method, path, status, and elapsed milliseconds along with the
request id stamped by RequestIDMiddleware. Kept intentionally simple so
that it does not interfere with uvicorn's own access log.
"""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.access")


SLOW_REQUEST_MS = 1000.0


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        rid = getattr(request.state, "request_id", "-")
        if response.status_code >= 500:
            log = logger.warning
        elif elapsed_ms > SLOW_REQUEST_MS:
            log = logger.warning
        else:
            log = logger.info
        log(
            "%s %s -> %d in %.1fms [rid=%s]",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            rid,
        )
        return response
