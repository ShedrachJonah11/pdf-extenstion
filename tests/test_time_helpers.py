from datetime import timezone

from app.utils.time_helpers import parse_iso, utcnow_iso


def test_utcnow_iso_returns_offset_aware_string() -> None:
    ts = utcnow_iso()
    assert isinstance(ts, str)
    assert "+00:00" in ts or ts.endswith("Z") or "T" in ts


def test_parse_iso_round_trip_through_utcnow_iso() -> None:
    ts = utcnow_iso()
    dt = parse_iso(ts)
    assert dt is not None
    assert dt.tzinfo == timezone.utc


def test_parse_iso_handles_naive_input() -> None:
    dt = parse_iso("2026-01-01T00:00:00")
    assert dt is not None
    assert dt.tzinfo == timezone.utc


def test_parse_iso_returns_none_on_garbage() -> None:
    assert parse_iso("not a date") is None
    assert parse_iso("") is None
