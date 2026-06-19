"""Shared pytest fixtures.

The tests intentionally avoid heavy ML dependencies (sentence-transformers,
faiss). We patch them with deterministic fakes so the suite runs in under
a second on CI.
"""

from __future__ import annotations

import os
import sys
import tempfile

import pytest

# Make sure secrets are deterministic for tests before importing settings
os.environ.setdefault("SECRET_KEY", "test-secret-for-pytest")
os.environ.setdefault("FAISS_PERSIST_DIR", tempfile.mkdtemp(prefix="faiss_tests_"))

# Ensure the project root is on sys.path for `import app`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def tmp_persist_dir(monkeypatch, tmp_path):
    """Point the FAISS persist dir at a fresh tmp directory per test."""
    from app import config as cfg

    monkeypatch.setattr(cfg.settings, "faiss_persist_dir", str(tmp_path), raising=False)
    return tmp_path
