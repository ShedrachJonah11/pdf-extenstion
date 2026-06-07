"""Request ID middleware.

Each incoming request is tagged with an X-Request-ID header. If the client
sends one we trust it; otherwise we generate a short hex id. The id is
stamped on the response so it can be correlated with logs.
"""

from __future__ import annotations

import logging
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.constants import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    MAX_INBOUND_LENGTH = 128

    async def dispatch(self, request: Request, call_next) -> Response:
        inbound = request.headers.get(REQUEST_ID_HEADER, "").strip()
        if inbound and len(inbound) <= self.MAX_INBOUND_LENGTH:
            rid = inbound
        else:
            rid = uuid4().hex[:12]
        request.state.request_id = rid
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = rid
        return response
