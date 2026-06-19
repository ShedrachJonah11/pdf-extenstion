"""End-to-end test for /health using FastAPI's TestClient.

This is deliberately the only TestClient test in the suite — booting the
full app pulls in sentence-transformers and faiss, so we keep it limited
to the lightest route that does not load the embedding model.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(scope="module")
def client():
    try:
        import faiss  # noqa: F401
        import sentence_transformers  # noqa: F401
    except Exception:
        pytest.skip("faiss/sentence-transformers not installed in this environment")

    from fastapi.testclient import TestClient

    main = importlib.import_module("app.main")
    with TestClient(main.app) as c:
        yield c


def test_health_returns_200(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_payload_shape(client) -> None:
    payload = client.get("/health").json()
    assert payload["status"] == "healthy"
    assert "llm_backend" in payload
    assert "documents_loaded" in payload
    assert "version" in payload
