from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from pypdf import PdfReader

from app.constants import CHUNK_OVERLAP_TOKENS, CHUNK_TARGET_TOKENS, MIN_CHUNK_CHARS
from app.utils.text import normalize_whitespace, strip_control_chars

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    text: str
    page: int
    chunk_index: int


@dataclass
class PdfMetadata:
    title: str | None
    author: str | None
    subject: str | None
    creator: str | None
    producer: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "creator": self.creator,
            "producer": self.producer,
        }


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def extract_metadata(pdf_bytes: bytes) -> PdfMetadata:
    """Pull title/author/etc. from the PDF info dict, when available."""
    reader = PdfReader(pdf_bytes)
    info = reader.metadata or {}
    return PdfMetadata(
        title=info.get("/Title"),
        author=info.get("/Author"),
        subject=info.get("/Subject"),
        creator=info.get("/Creator"),
        producer=info.get("/Producer"),
    )


def page_count(pdf_bytes: bytes) -> int:
    """Quick page count without running text extraction."""
    return len(PdfReader(pdf_bytes).pages)


def extract_text(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Extract text from PDF bytes. Returns list of (page_number, text)."""
    reader = PdfReader(pdf_bytes)
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        text = normalize_whitespace(strip_control_chars(raw))
        if text:
            pages.append((i + 1, text))
    total_pages = len(reader.pages)
    logger.info("Extracted text from %d / %d pages", len(pages), total_pages)
    return pages


def chunk_text(
    pages: list[tuple[int, str]],
    target_tokens: int = CHUNK_TARGET_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
) -> list[TextChunk]:
    """Split page text into overlapping chunks of ~target_tokens.

    ValueError is raised for nonsensical parameters so the caller cannot
    accidentally produce a degenerate chunking that loops forever or
    drops content silently.
    """
    if target_tokens <= 0:
        raise ValueError("target_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= target_tokens:
        raise ValueError("overlap_tokens must be in [0, target_tokens)")
    chunks: list[TextChunk] = []
    chunk_index = 0

    for page_num, page_text in pages:
        sentences = re.split(r"(?<=[.!?])\s+", page_text)
        current: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sent_tokens = _estimate_tokens(sentence)

            if current_tokens + sent_tokens > target_tokens and current:
                chunk_text_str = " ".join(current).strip()
                if chunk_text_str:
                    chunks.append(TextChunk(
                        text=chunk_text_str,
                        page=page_num,
                        chunk_index=chunk_index,
                    ))
                    chunk_index += 1

                # Keep overlap
                overlap: list[str] = []
                overlap_count = 0
                for s in reversed(current):
                    t = _estimate_tokens(s)
                    if overlap_count + t > overlap_tokens:
                        break
                    overlap.insert(0, s)
                    overlap_count += t
                current = overlap
                current_tokens = overlap_count

            current.append(sentence)
            current_tokens += sent_tokens

        # Flush remaining
        if current:
            chunk_text_str = " ".join(current).strip()
            if chunk_text_str and len(chunk_text_str) >= MIN_CHUNK_CHARS:
                chunks.append(TextChunk(
                    text=chunk_text_str,
                    page=page_num,
                    chunk_index=chunk_index,
                ))
                chunk_index += 1

    logger.info("Created %d chunks from %d pages", len(chunks), len(pages))
    return chunks
