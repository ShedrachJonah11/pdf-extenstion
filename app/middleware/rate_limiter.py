"""Per-IP rate limiter shared by the API routers.

Wraps `slowapi.Limiter` with a small helper that prefers the
`X-Forwarded-For` header when the request comes through a trusted
reverse proxy.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First entry is the original client IP.
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_client_key, default_limits=[settings.rate_limit])
