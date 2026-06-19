from app.utils.text import normalize_whitespace, strip_control_chars, truncate


def test_normalize_whitespace_collapses_runs() -> None:
    assert normalize_whitespace("hello\n\n  world\t!") == "hello world !"


def test_normalize_whitespace_trims_edges() -> None:
    assert normalize_whitespace("   trim me   ") == "trim me"


def test_strip_control_chars_removes_nul() -> None:
    assert strip_control_chars("foo\x00bar") == "foobar"


def test_strip_control_chars_preserves_newline_tab() -> None:
    assert strip_control_chars("a\tb\nc") == "a\tb\nc"


def test_strip_control_chars_strips_bell() -> None:
    assert strip_control_chars("foo\x07bar") == "foobar"


def test_truncate_short_strings_unchanged() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_adds_ellipsis() -> None:
    out = truncate("hello world", 6)
    assert out.endswith("…")
    assert len(out) == 6


def test_truncate_zero_length() -> None:
    assert truncate("anything", 0) == ""
