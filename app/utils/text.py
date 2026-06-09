"""Small text helpers used across services."""

from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")
_CONTROL_CHARS = "".join(chr(c) for c in range(32) if c not in (9, 10, 13))


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces and trim ends."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def strip_control_chars(text: str) -> str:
    """Remove NULs and other PDF artefacts that confuse downstream tools.

    Tab (9), newline (10), and carriage return (13) are kept so structure
    inside extracted text survives.
    """
    if not text:
        return text
    return text.translate({ord(c): None for c in _CONTROL_CHARS})


def truncate(text: str, max_chars: int, ellipsis: str = "…") -> str:
    """Shorten *text* to at most *max_chars*, appending an ellipsis if cut."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    cutoff = max(0, max_chars - len(ellipsis))
    return text[:cutoff] + ellipsis
