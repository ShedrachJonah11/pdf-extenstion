# Troubleshooting

## "No OPENAI_API_KEY found — using mock LLM backend"

This is informational, not an error. The service falls back to a mock
backend when no key is configured. Set `OPENAI_API_KEY` to enable real
answers.

## 401 Invalid or expired token

The JWT either failed to decode or the `sub` claim points at a user that
is no longer in the (in-memory) user store. The most common cause is a
restart between login and a subsequent request.

## 413 File exceeds Nmb limit

Adjust `MAX_UPLOAD_SIZE_MB`. Also make sure the reverse proxy has at
least as large a body limit configured (see `docs/deployment.md`).

## 422 Body does not look like a PDF

The upload endpoint requires the first bytes of the body to be the
`%PDF-` magic header. Make sure the client really sent a PDF and the
multipart field is named `file`.

## 422 Could not extract any text from the PDF

The PDF was probably image-only (scanned). This service does not run
OCR; pre-process such PDFs before uploading.

## Mock answers in production

Confirm that `OPENAI_API_KEY` is set in the running container, not just
locally. `GET /health` will report `llm_backend: "mock"` when the mock
is active.

## CORS errors in the browser

Ensure `CORS_ALLOW_ORIGINS` includes the frontend origin. The default
`*` is fine for local dev but should not be used in production.
