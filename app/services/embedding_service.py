from __future__ import annotations

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
_model_dim: int | None = None

# Batch size for embedding to keep memory bounded on large uploads.
EMBED_BATCH_SIZE = 64

# Token length cap for an individual embed call. Most sentence-transformer
# models truncate at 512 tokens; we mirror that here to avoid surprises.
EMBED_MAX_INPUT_CHARS = 8000


def get_model() -> SentenceTransformer:
    global _model, _model_dim
    if _model is None:
        import time

        t0 = time.perf_counter()
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        _model_dim = _model.get_sentence_embedding_dimension()
        elapsed = time.perf_counter() - t0
        logger.info(
            "Embedding model loaded (dim=%d) in %.1fs", _model_dim, elapsed
        )
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of texts. Returns (n, dim) float32 array.

    Batches internally so very large documents do not balloon memory.
    """
    if not texts:
        return np.zeros((0, get_embedding_dim()), dtype=np.float32)
    if any(not t.strip() for t in texts):
        raise ValueError("embed_texts received a blank entry")
    capped = [t if len(t) <= EMBED_MAX_INPUT_CHARS else t[:EMBED_MAX_INPUT_CHARS] for t in texts]
    model = get_model()
    embeddings = model.encode(
        capped,
        batch_size=EMBED_BATCH_SIZE,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return embeddings.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query. Returns (1, dim) float32 array."""
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    return embed_texts([query])


def get_embedding_dim() -> int:
    if _model_dim is not None:
        return _model_dim
    return get_model().get_sentence_embedding_dimension()


def reset_model_cache() -> None:
    """Drop the cached model. Useful for tests and config reloads."""
    global _model, _model_dim
    _model = None
    _model_dim = None
