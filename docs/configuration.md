# Configuration reference

All settings are read from environment variables (or a `.env` file at the
project root). Defaults live in `app/config.py`.

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `SECRET_KEY` | str | `change-me-...` | JWT signing key. **Set this in production.** |
| `ALGORITHM` | str | `HS256` | JWT algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `60` | Access-token TTL. |
| `OPENAI_API_KEY` | str | (empty) | If empty, the mock LLM is used. |
| `OPENAI_MODEL` | str | `gpt-4o-mini` | Chat model when OpenAI is configured. |
| `EMBEDDING_MODEL` | str | `all-MiniLM-L6-v2` | Sentence-transformer model. |
| `FAISS_PERSIST_DIR` | str | `./faiss_indexes` | Where FAISS indexes live on disk. |
| `MAX_UPLOAD_SIZE_MB` | int | `50` | Hard cap on PDF upload size. |
| `RATE_LIMIT` | str | `20/minute` | Default per-IP per-route limit. |
| `LOG_LEVEL` | str | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `CORS_ALLOW_ORIGINS` | str | `*` | Comma-separated origin list. |
| `LLM_REQUEST_TIMEOUT` | float | `30.0` | Per-attempt timeout in seconds for upstream LLM calls. |

## Examples

Local dev:

```bash
SECRET_KEY=local-dev-secret
LOG_LEVEL=DEBUG
CORS_ALLOW_ORIGINS=*
```

Production behind a known frontend:

```bash
SECRET_KEY=<32 random bytes>
LOG_LEVEL=INFO
CORS_ALLOW_ORIGINS=https://app.example.com,https://admin.example.com
MAX_UPLOAD_SIZE_MB=25
RATE_LIMIT=60/minute
```
