# Changelog

All notable changes to this project will be documented in this file.
The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Versioned API: routes are now mounted under both `/` (legacy) and
  `/v1/` prefixes so new clients can pin to a stable surface.
- Typed exception hierarchy (`app.exceptions`) with stable `error_code`
  values, plus a global handler emitting structured JSON.
- Document ownership: uploads tag the document with the uploader and the
  list/chat/delete endpoints filter by owner.
- `top_k` parameter on `ChatRequest`, defaulting to 5 and capped at 20.
- `/auth/me` and `/auth/refresh` endpoints.
- Filename search and pagination on `/documents`.
- Bulk delete endpoint `POST /documents/bulk-delete`.
- Document detail endpoint `GET /documents/{id}` with sample chunks.
- Conversation history per (user, document) with bounded ring buffer.
- Conversation-aware prompt template, plumbed through ask_question.
- Retry-with-backoff helper applied to the OpenAI backend.
- `X-Request-ID` middleware plus access-log middleware.
- `/health` now reports uptime, version, and registered user count.
- Password complexity check (length, letter, digit, blacklist).
- `LLMError` (502) wraps upstream OpenAI failures.
- `LLMTimeoutError` (504) for per-attempt OpenAI timeouts.
- `LLM_REQUEST_TIMEOUT` setting (default 30 seconds).
- `/auth/logout` clears the caller's conversation history.
- Document list now supports `?sort=created_at|filename`.
- LLM prompt builders cap output at `MAX_PROMPT_CHARS`.
- `ChatResponse.cited_pages` property listing unique pages used.
- `GET /ready` liveness probe that does not load the embedding model.

### Changed
- Chunk sizes and other tunables centralized in `app.constants`.
- Username validation now restricts to letters, digits, `_`, `-` and `.`.
- Trailing micro-chunks (< `MIN_CHUNK_CHARS`) are dropped before embedding.
- Extracted page text is whitespace-normalized and stripped of NULs.
- Rate limiter now keys on the original client IP when behind a proxy.
- LLM backend construction is deferred via a lazy proxy.
- Upload rejects empty bodies and bodies missing the `%PDF-` magic.

### Removed
- Nothing yet.
