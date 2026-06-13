"""Single source of truth for on-disk paths used by the vector store.

Keeping these names in one place makes it easier to migrate the layout
later — e.g. moving `metadata.json` under a `meta/` subdirectory.
"""

from __future__ import annotations

from pathlib import Path

METADATA_FILE = "metadata.json"
INDEX_FILE = "index.faiss"


def doc_dir(persist_root: Path, document_id: str) -> Path:
    return persist_root / document_id


def metadata_path(persist_root: Path, document_id: str) -> Path:
    return doc_dir(persist_root, document_id) / METADATA_FILE


def index_path(persist_root: Path, document_id: str) -> Path:
    return doc_dir(persist_root, document_id) / INDEX_FILE
