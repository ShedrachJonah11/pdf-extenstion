from app import constants


def test_top_k_bounds_are_consistent() -> None:
    assert 1 <= constants.DEFAULT_TOP_K <= constants.MAX_TOP_K


def test_chunk_sizes_are_sane() -> None:
    assert constants.CHUNK_OVERLAP_TOKENS < constants.CHUNK_TARGET_TOKENS
    assert constants.CHUNK_TARGET_TOKENS > 0


def test_api_prefix_is_versioned() -> None:
    assert constants.API_V1_PREFIX.startswith("/v")


def test_pdf_content_types_includes_application_pdf() -> None:
    assert "application/pdf" in constants.PDF_CONTENT_TYPES
