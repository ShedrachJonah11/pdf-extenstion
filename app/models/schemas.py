from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


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
    document_id: str
    question: str = Field(..., min_length=1, max_length=2000)


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


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    total_pages: int
    total_chunks: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    llm_backend: str
    documents_loaded: int
