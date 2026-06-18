"""Reusable FastAPI dependencies.

Centralizing dependencies in one module keeps route signatures short and
makes it easier to swap in a test override.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.auth.auth import get_current_user
from app.services.vector_store import DocumentIndex, vector_store


async def get_owned_document(
    document_id: str,
    user: str = Depends(get_current_user),
) -> DocumentIndex:
    """Resolve a DocumentIndex by id and verify the caller owns it."""
    doc = vector_store.get(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.owner is not None and doc.owner != user:
        raise HTTPException(status_code=403, detail="You do not own this document")
    return doc
