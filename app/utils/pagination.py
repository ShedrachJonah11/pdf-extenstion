"""Pagination helpers shared by list endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, TypeVar

T = TypeVar("T")

MIN_PAGE = 1
MAX_PAGE_SIZE = 200


@dataclass
class Page:
    page: int
    page_size: int

    @property
    def start(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def end(self) -> int:
        return self.start + self.page_size


def validate_page_params(page: int, page_size: int) -> Page:
    if page < MIN_PAGE:
        raise ValueError(f"page must be >= {MIN_PAGE}")
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}")
    return Page(page=page, page_size=page_size)


def slice_page(items: Sequence[T], page: Page) -> list[T]:
    return list(items[page.start : page.end])
