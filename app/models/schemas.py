from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.constants import (
    DEFAULT_TOP_K,
    MAX_PASSWORD_LENGTH,
    MAX_TOP_K,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=MIN_USERNAME_LENGTH, max_length=MAX_USERNAME_LENGTH)
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("username")
    @classmethod
    def _username_charset(cls, value: str) -> str:
        if not all(c.isalnum() or c in {"_", "-", "."} for c in value):
            raise ValueError(
                "username may only contain letters, digits, '_', '-' and '.'"
            )
        return value


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    total_pages: int
    total_chunks: int
    message: str = "Document processed successfully"


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    document_id: str = Field(..., min_length=1, max_length=64)
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)

    @field_validator("question")
    @classmethod
    def _question_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be blank")
        return stripped


class RetrievedChunk(BaseModel):
    text: str
    page: int
    chunk_index: int
    score: float


class ChatResponse(BaseModel):
    answer: str
    document_id: str
    question: str
    retrieved_chunks: List[RetrievedChunk]
    token_count: Optional[int] = None
    model_used: str

    @property
    def cited_pages(self) -> List[int]:
        seen: list[int] = []
        for c in self.retrieved_chunks:
            if c.page not in seen:
                seen.append(c.page)
        return seen


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    total_pages: int
    total_chunks: int
    owner: Optional[str] = None
    created_at: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int
    page: int = 1
    page_size: int = 50


class ChunkPreview(BaseModel):
    chunk_index: int
    page: int
    text: str


class DocumentDetail(DocumentInfo):
    sample_chunks: List[ChunkPreview] = []


# ── Error envelope ────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Stable error envelope returned by the global exception handler."""

    error_code: str
    message: str
    request_id: Optional[str] = None


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    llm_backend: str
    documents_loaded: int
    version: str = "1.0.0"
    uptime_seconds: Optional[float] = None
    users_registered: Optional[int] = None


# ── Bulk delete ───────────────────────────────────────────────────────────────

class BulkDeleteRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=1, max_length=100)


class BulkDeleteResponse(BaseModel):
    deleted: int
    not_found: List[str]
    forbidden: List[str]


# ── Conversation ──────────────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    question: str
    answer: str


class ConversationHistoryResponse(BaseModel):
    document_id: str
    turns: List[ConversationTurn]
    total: int = 0
