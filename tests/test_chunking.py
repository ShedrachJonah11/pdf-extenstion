"""Unit tests for the chunker.

These exercise chunk_text directly with hand-constructed (page, text)
inputs, which avoids depending on a real PDF parser.
"""

from app.services.pdf_service import TextChunk, chunk_text


def _page(p: int, text: str) -> tuple[int, str]:
    return (p, text)


def test_chunker_returns_text_chunks() -> None:
    chunks = chunk_text([_page(1, "Hello world. This is a sentence.")])
    assert all(isinstance(c, TextChunk) for c in chunks)


def test_chunker_assigns_page_numbers() -> None:
    chunks = chunk_text(
        [_page(1, "Hello world."), _page(7, "Different page text here.")]
    )
    pages = {c.page for c in chunks}
    assert pages.issuperset({1, 7})


def test_chunker_assigns_monotonically_increasing_indexes() -> None:
    chunks = chunk_text(
        [_page(1, "Sentence one. Sentence two. Sentence three.")]
    )
    indexes = [c.chunk_index for c in chunks]
    assert indexes == sorted(set(indexes))


def test_chunker_respects_target_tokens() -> None:
    big = "Hello world. " * 400  # ~ many tokens
    chunks = chunk_text([_page(1, big)], target_tokens=100, overlap_tokens=10)
    # If chunking works, we should get more than one chunk
    assert len(chunks) > 1


def test_chunker_handles_empty_input() -> None:
    assert chunk_text([]) == []


def test_chunker_rejects_zero_target_tokens() -> None:
    import pytest
    with pytest.raises(ValueError):
        chunk_text([_page(1, "hi")], target_tokens=0, overlap_tokens=0)


def test_chunker_rejects_overlap_ge_target() -> None:
    import pytest
    with pytest.raises(ValueError):
        chunk_text([_page(1, "hi")], target_tokens=10, overlap_tokens=10)
