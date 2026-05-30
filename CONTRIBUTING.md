# Contributing

Thanks for your interest in improving this project. The bar for changes
is small but real: please make sure the tests still pass and the code
stays consistent with the rest of the file.

## Local setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

## Running the suite

```bash
make test        # pytest
make lint        # ruff check
make format      # ruff format
```

The full suite avoids heavy ML dependencies for speed. If you need an
end-to-end test that exercises the real embedding model or FAISS, mark
it with `@pytest.mark.slow` and gate it behind `pytest -m slow`.

## Commit style

Use Conventional Commits — one of `feat:`, `fix:`, `refactor:`, `docs:`,
`chore:`, `test:`, `ci:`. Keep the subject under ~72 characters and
imperative ("add", not "adds").

## Architecture notes

The full architecture overview lives in [`docs/architecture.md`](docs/architecture.md).

## Adding a new endpoint — checklist

1. Add the route to `app/api/routes.py`. Re-use the existing tag.
2. Add request/response schemas to `app/models/schemas.py`.
3. If the route touches a document, depend on `get_owned_document` so
   the 404/403 checks stay consistent.
4. Raise typed errors from `app.exceptions` rather than `HTTPException`
   where possible — the global handler will turn them into the standard
   error envelope.
5. Update `docs/api.md` and `CHANGELOG.md`.
6. Add tests under `tests/` for any non-trivial logic.
