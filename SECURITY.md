# Security policy

## Reporting a vulnerability

If you think you've found a security issue please email the maintainer
rather than opening a public GitHub issue. We will respond within five
business days.

## Hardening checklist

This project is small and intended primarily for self-hosting. The
following are required before a production deployment:

- **`SECRET_KEY`** must be set to a random 32+ byte value. Do not leave
  the default in `.env.example` in place.
- **CORS** is set to `allow_origins=["*"]` to make local development
  easier. Lock it down via environment configuration for any internet-
  facing deployment.
- **Rate limiting** is per-IP via `slowapi`. Add a layer 7 reverse proxy
  with its own limits if you expect adversarial traffic.
- **Upload size cap** is enforced at the API layer (`MAX_UPLOAD_SIZE_MB`)
  but not at the reverse-proxy layer. Configure a similar cap there.
- **OpenAI key** is read from `OPENAI_API_KEY`. The container image does
  not bake it in.

## Known limitations

- The user store is in-memory and resets on restart.
- JWT tokens are not revokable; there is no logout list.
- FAISS indexes are not encrypted on disk.
