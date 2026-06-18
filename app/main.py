import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import auth_router, router  # noqa: I001 — explicit ordering for FastAPI app
from app.config import settings
from app.constants import API_V1_PREFIX
from app.error_handlers import register_error_handlers
from app.middleware.access_log import AccessLogMiddleware
from app.middleware.rate_limiter import limiter
from app.middleware.request_id import RequestIDMiddleware

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── App ───────────────────────────────────────────────────────────────────────

from app import __version__

logger = logging.getLogger(__name__)
logger.info("Starting PDF AI Backend v%s", __version__)

app = FastAPI(
    title="PDF AI Backend",
    description="RAG-powered document Q&A API",
    version=__version__,
    contact={"name": "Maintainers", "url": "https://github.com/your-org/pdf-ai-backend"},
    license_info={"name": "MIT"},
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request observability (order matters: request id first, then access log)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestIDMiddleware)

# Error handlers
register_error_handlers(app)

# Routes
app.include_router(auth_router)
app.include_router(router)

# Versioned mirror (preferred for new clients)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(router, prefix=API_V1_PREFIX)
