"""Centralized constants for the PDF AI backend.

Keep magic numbers and string literals here so that callers reference a
single named constant instead of repeating values across the codebase.
"""

from __future__ import annotations

# ── Chunking ──────────────────────────────────────────────────────────────────

CHUNK_TARGET_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
MIN_CHUNK_CHARS = 20

# ── Retrieval ─────────────────────────────────────────────────────────────────

DEFAULT_TOP_K = 5
MAX_TOP_K = 20

# ── LLM ───────────────────────────────────────────────────────────────────────

DEFAULT_LLM_TEMPERATURE = 0.2
DEFAULT_LLM_MAX_TOKENS = 1024

# ── Upload ────────────────────────────────────────────────────────────────────

PDF_CONTENT_TYPES = ("application/pdf", "application/octet-stream")
PDF_EXTENSION = ".pdf"

# ── Auth ──────────────────────────────────────────────────────────────────────

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128

# ── API ───────────────────────────────────────────────────────────────────────

API_V1_PREFIX = "/v1"
REQUEST_ID_HEADER = "X-Request-ID"

# ── Documents ─────────────────────────────────────────────────────────────────

DOCUMENT_ID_LENGTH = 16  # uuid4().hex[:16]
DEFAULT_SAMPLE_CHUNKS = 3
MAX_SAMPLE_CHUNKS = 20
SAMPLE_CHUNK_PREVIEW_CHARS = 300

# ── Sorting ───────────────────────────────────────────────────────────────────

DOCUMENT_SORT_KEYS = ("created_at", "filename")
