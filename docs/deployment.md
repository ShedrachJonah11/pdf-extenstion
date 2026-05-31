# Deployment notes

This project is intended to be deployed as a single FastAPI process behind
a reverse proxy. Both single-container and compose-based deployments are
supported.

## Single container

```bash
docker build -t pdf-ai-backend .
docker run --rm -p 8000:8000 \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v faiss-indexes:/app/faiss_indexes \
  pdf-ai-backend
```

## docker-compose

```bash
docker compose up -d
```

The `docker-compose.yml` mounts a named volume at `/app/faiss_indexes`
so document indexes survive container restarts.

## Behind a reverse proxy

Recommended Nginx snippet:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_buffering off;            # required for /chat/stream SSE
    client_max_body_size 60M;       # match MAX_UPLOAD_SIZE_MB
}
```

## Pre-flight checklist

- [ ] `SECRET_KEY` is a random 32+ byte value (not the default)
- [ ] `CORS_ALLOW_ORIGINS` is a comma-separated list, not `*`
- [ ] `OPENAI_API_KEY` is set (or you intentionally want the mock)
- [ ] The `faiss_indexes` directory is on a persistent volume
- [ ] The reverse proxy enforces a request size cap
