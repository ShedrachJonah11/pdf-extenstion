from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from app.config import settings
from app.services.pdf_service import TextChunk
from app.services.storage_paths import (
    INDEX_FILE,
    METADATA_FILE,
    doc_dir,
    index_path,
    metadata_path,
)
from app.utils.time_helpers import utcnow_iso

logger = logging.getLogger(__name__)


class DocumentIndex:
    """FAISS index + metadata for a single document.

    The index is normalized so inner product == cosine similarity. Scores
    returned by search() are therefore in [-1, 1] with higher being more
    relevant.
    """

    def __init__(
        self,
        document_id: str,
        filename: str,
        total_pages: int,
        chunks: list[TextChunk],
        index: faiss.Index,
        owner: str | None = None,
        created_at: str | None = None,
    ) -> None:
        self.document_id = document_id
        self.filename = filename
        self.total_pages = total_pages
        self.chunks = chunks
        self.index = index
        self.owner = owner
        self.created_at = created_at or utcnow_iso()

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[tuple[TextChunk, float]]:
        """Return top_k (chunk, score) pairs sorted by relevance."""
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.chunks)))
        results: list[tuple[TextChunk, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.chunks[idx], float(dist)))
        return results


class VectorStore:
    """In-memory store mapping document_id → DocumentIndex with disk persistence."""

    def __init__(self) -> None:
        self._indexes: dict[str, DocumentIndex] = {}
        self._load_persisted()

    def _load_persisted(self) -> None:
        persist_dir = settings.persist_path
        meta_files = sorted(persist_dir.glob(f"*/{METADATA_FILE}"))
        failed = 0
        for meta_path in meta_files:
            try:
                self._load_document(meta_path.parent)
            except Exception:
                failed += 1
                logger.exception("Failed to load persisted index from %s", meta_path.parent)

        if self._indexes:
            logger.info(
                "Loaded %d persisted document indexes (%d failed)",
                len(self._indexes),
                failed,
            )

    def _load_document(self, doc_dir_path: Path) -> None:
        meta = json.loads((doc_dir_path / METADATA_FILE).read_text())
        index = faiss.read_index(str(doc_dir_path / INDEX_FILE))
        chunks = [TextChunk(**c) for c in meta["chunks"]]
        doc_index = DocumentIndex(
            document_id=meta["document_id"],
            filename=meta["filename"],
            total_pages=meta["total_pages"],
            chunks=chunks,
            index=index,
            owner=meta.get("owner"),
            created_at=meta.get("created_at"),
        )
        self._indexes[meta["document_id"]] = doc_index

    def add_document(
        self,
        document_id: str,
        filename: str,
        total_pages: int,
        chunks: list[TextChunk],
        embeddings: np.ndarray,
        owner: str | None = None,
    ) -> DocumentIndex:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # inner product (cosine after normalization)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)

        doc_index = DocumentIndex(
            document_id=document_id,
            filename=filename,
            total_pages=total_pages,
            chunks=chunks,
            index=index,
            owner=owner,
        )
        self._indexes[document_id] = doc_index
        self._persist(doc_index)
        logger.info("Added document %s (%d chunks)", document_id, len(chunks))
        return doc_index

    def _persist(self, doc_index: DocumentIndex) -> None:
        root = settings.persist_path
        doc_dir(root, doc_index.document_id).mkdir(parents=True, exist_ok=True)

        faiss.write_index(doc_index.index, str(index_path(root, doc_index.document_id)))

        meta = {
            "document_id": doc_index.document_id,
            "filename": doc_index.filename,
            "total_pages": doc_index.total_pages,
            "owner": doc_index.owner,
            "created_at": doc_index.created_at,
            "chunks": [asdict(c) for c in doc_index.chunks],
        }
        metadata_path(root, doc_index.document_id).write_text(
            json.dumps(meta, ensure_ascii=False)
        )

    def get(self, document_id: str) -> DocumentIndex | None:
        return self._indexes.get(document_id)

    def exists(self, document_id: str) -> bool:
        return document_id in self._indexes

    def delete(self, document_id: str) -> bool:
        if document_id not in self._indexes:
            return False
        del self._indexes[document_id]
        target = doc_dir(settings.persist_path, document_id)
        if target.exists():
            for f in target.iterdir():
                try:
                    f.unlink()
                except FileNotFoundError:
                    pass
            try:
                target.rmdir()
            except OSError:
                logger.warning("Could not remove dir %s (non-empty?)", target)
        return True

    def list_documents(self, owner: str | None = None) -> list[DocumentIndex]:
        if owner is None:
            return list(self._indexes.values())
        return [d for d in self._indexes.values() if d.owner == owner]

    def find_by_filename(self, owner: str, needle: str) -> list[DocumentIndex]:
        needle_lower = needle.lower()
        return [
            d for d in self._indexes.values()
            if d.owner == owner and needle_lower in d.filename.lower()
        ]

    def count_for(self, owner: str) -> int:
        return sum(1 for d in self._indexes.values() if d.owner == owner)

    def total_chunks(self) -> int:
        return sum(len(d.chunks) for d in self._indexes.values())

    def total_chunks_for(self, owner: str) -> int:
        return sum(len(d.chunks) for d in self._indexes.values() if d.owner == owner)

    @property
    def document_count(self) -> int:
        return len(self._indexes)


# Singleton
vector_store = VectorStore()
