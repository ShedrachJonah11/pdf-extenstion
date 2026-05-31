# Testing

The suite is intentionally fast: it does not load the embedding model or
hit FAISS in the default configuration. Heavy paths are covered by unit
tests against the pure-Python parts of the code (chunking, validation,
retry, conversation history, token counting fallback).

## Run

```bash
make test                # everything
pytest tests/test_chunking.py    # one file
pytest -k retry           # by keyword
```

## Markers

- `slow` — tests that need the real embedding model or faiss. Not run by
  default; opt in with `pytest -m slow` once the model has been warmed
  up.

## What's covered

| Area | File |
| --- | --- |
| Constants | `tests/test_constants.py` |
| Schemas | `tests/test_schemas.py` |
| Exceptions | `tests/test_exceptions.py` |
| Retry helper | `tests/test_retry.py` |
| Auth | `tests/test_auth.py` |
| Password complexity | `tests/test_passwords.py` |
| Chunking | `tests/test_chunking.py` |
| LLM prompt/tokens | `tests/test_llm_prompt.py` |
| Conversation history | `tests/test_conversation.py` |
| Pagination | `tests/test_pagination.py` |
| Storage paths | `tests/test_storage_paths.py` |
| Text utils | `tests/test_text_utils.py` |
| Time helpers | `tests/test_time_helpers.py` |
| Health route (TestClient) | `tests/test_health_route.py` |
