from __future__ import annotations

import logging
from io import BytesIO
from uuid import uuid4

import faiss
import numpy as np

from app.models.schemas import (
    ChatResponse,
    RetrievedChunk,
    UploadResponse,
)
from app.services.embedding_service import embed_query, embed_texts
from app.services.llm_service import count_tokens, llm_backend
from app.services.pdf_service import chunk_text, extract_text
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


async def process_upload(filename: str, pdf_bytes: bytes) -> UploadResponse:
    """Full pipeline: extract → chunk → embed → store."""
    document_id = uuid4().hex[:16]

    pages = extract_text(BytesIO(pdf_bytes))
    if not pages:
        raise ValueError("Could not extract any text from the PDF")

    total_pages = max(p for p, _ in pages)
    chunks = chunk_text(pages)
    if not chunks:
        raise ValueError("No text chunks produced from the PDF")

    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)

    vector_store.add_document(
        document_id=document_id,
        filename=filename,
        total_pages=total_pages,
        chunks=chunks,
        embeddings=embeddings,
    )

    return UploadResponse(
        document_id=document_id,
        filename=filename,
        total_pages=total_pages,
        total_chunks=len(chunks),
    )


async def ask_question(document_id: str, question: str) -> ChatResponse:
    """Embed question → retrieve → generate answer."""
    doc_index = vector_store.get(document_id)
    if doc_index is None:
        raise KeyError(f"Document '{document_id}' not found")

    query_emb = embed_query(question)
    faiss.normalize_L2(query_emb)

    results = doc_index.search(query_emb, top_k=5)

    context = "\n\n---\n\n".join(
        f"[Page {chunk.page}] {chunk.text}" for chunk, _ in results
    )

    prompt = llm_backend.build_prompt(context=context, question=question)
    answer = await llm_backend.generate(prompt)

    retrieved = [
        RetrievedChunk(
            text=chunk.text,
            page=chunk.page,
            chunk_index=chunk.chunk_index,
            score=round(score, 4),
        )
        for chunk, score in results
    ]

    return ChatResponse(
        answer=answer,
        document_id=document_id,
        question=question,
        retrieved_chunks=retrieved,
        token_count=count_tokens(prompt + answer),
        model_used=llm_backend.name,
    )
