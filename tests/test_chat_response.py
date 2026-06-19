from app.models.schemas import ChatResponse, RetrievedChunk


def _chunk(page: int, text: str = "x") -> RetrievedChunk:
    return RetrievedChunk(text=text, page=page, chunk_index=0, score=0.5)


def test_cited_pages_preserves_first_occurrence_order() -> None:
    resp = ChatResponse(
        answer="ok",
        document_id="d",
        question="q",
        retrieved_chunks=[_chunk(3), _chunk(1), _chunk(3), _chunk(2)],
        model_used="mock",
    )
    assert resp.cited_pages == [3, 1, 2]


def test_cited_pages_empty_when_no_chunks() -> None:
    resp = ChatResponse(
        answer="ok",
        document_id="d",
        question="q",
        retrieved_chunks=[],
        model_used="mock",
    )
    assert resp.cited_pages == []
