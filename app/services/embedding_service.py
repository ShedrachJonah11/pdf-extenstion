from __future__ import annotations

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded (dim=%d)", _model.get_sentence_embedding_dimension())
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a list of texts. Returns (n, dim) float32 array."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query. Returns (1, dim) float32 array."""
    return embed_texts([query])


def get_embedding_dim() -> int:
    return get_model().get_sentence_embedding_dimension()
