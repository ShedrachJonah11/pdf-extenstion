"""Time-related helpers, mainly for monotonic timing and ISO timestamps."""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def parse_iso(timestamp: str) -> datetime | None:
    """Parse an ISO 8601 string, returning None on failure."""
    try:
        dt = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
