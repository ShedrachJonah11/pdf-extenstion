from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from app.config import settings
from app.services.pdf_service import TextChunk

logger = logging.getLogger(__name__)


class DocumentIndex:
    """FAISS index + metadata for a single document."""

    def __init__(
        self,
        document_id: str,
        filename: str,
        total_pages: int,
        chunks: list[TextChunk],
        index: faiss.Index,
    ) -> None:
        self.document_id = document_id
        self.filename = filename
        self.total_pages = total_pages
        self.chunks = chunks
        self.index = index

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
        meta_files = list(persist_dir.glob("*/metadata.json"))
        for meta_path in meta_files:
            try:
                self._load_document(meta_path.parent)
            except Exception:
                logger.exception("Failed to load persisted index from %s", meta_path.parent)

        if self._indexes:
            logger.info("Loaded %d persisted document indexes", len(self._indexes))

    def _load_document(self, doc_dir: Path) -> None:
        meta = json.loads((doc_dir / "metadata.json").read_text())
        index = faiss.read_index(str(doc_dir / "index.faiss"))
        chunks = [TextChunk(**c) for c in meta["chunks"]]
        doc_index = DocumentIndex(
            document_id=meta["document_id"],
            filename=meta["filename"],
            total_pages=meta["total_pages"],
            chunks=chunks,
            index=index,
        )
        self._indexes[meta["document_id"]] = doc_index

    def add_document(
        self,
        document_id: str,
        filename: str,
        total_pages: int,
        chunks: list[TextChunk],
        embeddings: np.ndarray,
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
        )
        self._indexes[document_id] = doc_index
        self._persist(doc_index)
        logger.info("Added document %s (%d chunks)", document_id, len(chunks))
        return doc_index

    def _persist(self, doc_index: DocumentIndex) -> None:
        doc_dir = settings.persist_path / doc_index.document_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        faiss.write_index(doc_index.index, str(doc_dir / "index.faiss"))

        meta = {
            "document_id": doc_index.document_id,
            "filename": doc_index.filename,
            "total_pages": doc_index.total_pages,
            "chunks": [asdict(c) for c in doc_index.chunks],
        }
        (doc_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False))

    def get(self, document_id: str) -> DocumentIndex | None:
        return self._indexes.get(document_id)

    def delete(self, document_id: str) -> bool:
        if document_id not in self._indexes:
            return False
        del self._indexes[document_id]
        doc_dir = settings.persist_path / document_id
        if doc_dir.exists():
            for f in doc_dir.iterdir():
                f.unlink()
            doc_dir.rmdir()
        return True

    def list_documents(self) -> list[DocumentIndex]:
        return list(self._indexes.values())

    @property
    def document_count(self) -> int:
        return len(self._indexes)


# Singleton
vector_store = VectorStore()
