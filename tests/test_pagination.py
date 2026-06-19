import pytest

from app.utils.pagination import Page, slice_page, validate_page_params


def test_page_offsets() -> None:
    p = Page(page=3, page_size=10)
    assert p.start == 20
    assert p.end == 30


def test_slice_page_returns_expected_window() -> None:
    items = list(range(25))
    assert slice_page(items, Page(page=2, page_size=10)) == list(range(10, 20))


def test_validate_page_params_happy_path() -> None:
    p = validate_page_params(1, 50)
    assert p.page == 1
    assert p.page_size == 50


def test_validate_page_rejects_zero_page() -> None:
    with pytest.raises(ValueError):
        validate_page_params(0, 50)


def test_validate_page_rejects_oversized_page_size() -> None:
    with pytest.raises(ValueError):
        validate_page_params(1, 999)


def test_validate_page_rejects_zero_page_size() -> None:
    with pytest.raises(ValueError):
        validate_page_params(1, 0)
