"""Global exception handlers for FastAPI.

Converts our typed AppError hierarchy into uniform JSON responses with a
stable error_code field. Unknown exceptions are logged and returned as a
generic 500 to avoid leaking internals.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_payload(error_code: str, message: str) -> dict[str, str]:
    return {"error_code": error_code, "message": message}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    rid = getattr(request.state, "request_id", None)
    payload = _error_payload(exc.error_code, exc.message)
    if rid:
        payload["request_id"] = rid
    return JSONResponse(status_code=exc.status_code, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = getattr(request.state, "request_id", None)
    logger.exception(
        "Unhandled exception on %s %s [rid=%s]",
        request.method,
        request.url.path,
        rid or "-",
    )
    payload = _error_payload("internal_error", "An unexpected error occurred")
    if rid:
        payload["request_id"] = rid
    return JSONResponse(status_code=500, content=payload)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
