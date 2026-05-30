# PDF AI Backend

A small FastAPI service that turns PDF documents into a question-answering
endpoint. Documents are chunked, embedded with a sentence-transformer, stored
in a per-document FAISS index, and answered with either OpenAI's chat
completion API or a deterministic mock backend when no API key is configured.

## Features

- JWT-based authentication
- PDF upload with per-file size cap and content-type validation
- Page-aware chunking with token-budgeted overlap
- Local embedding via `sentence-transformers/all-MiniLM-L6-v2` (default)
- FAISS inner-product index per document, persisted to disk
- Streaming chat responses (Server-Sent Events)
- Pluggable LLM backend (OpenAI / mock)
- Per-route rate limiting via `slowapi`

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for the interactive OpenAPI UI.

## Configuration

All settings come from environment variables (or a `.env` file). See
`.env.example` for the complete list.

| Variable | Default | Description |
| --- | --- | --- |
| `SECRET_KEY` | `change-me-...` | JWT signing key — set in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token TTL |
| `OPENAI_API_KEY` | (empty) | If set, real OpenAI backend is used |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model |
| `FAISS_PERSIST_DIR` | `./faiss_indexes` | Where indexes live on disk |
| `MAX_UPLOAD_SIZE_MB` | `50` | Upload cap |
| `RATE_LIMIT` | `20/minute` | Default per-route limit |

## Docker

```bash
docker build -t pdf-ai-backend .
docker run --rm -p 8000:8000 --env-file .env pdf-ai-backend
```

See `docker-compose.yml` for a local development stack with persistent
indexes.

## Project layout

See [`docs/architecture.md`](docs/architecture.md) for the module map and
pipeline diagrams. The configuration reference lives in
[`docs/configuration.md`](docs/configuration.md), the API reference in
[`docs/api.md`](docs/api.md), and the deployment guide in
[`docs/deployment.md`](docs/deployment.md).

## Status

The API surface has settled enough to be considered v1: routes mounted
at `/v1/...` are stable and changes to them will go through the normal
deprecation cycle described in `CHANGELOG.md`. Routes mounted at `/`
(without the `/v1` prefix) are kept for now but will be removed in a
future major release.

## License

MIT
