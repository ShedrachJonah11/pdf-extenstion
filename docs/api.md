# API reference

All routes are mounted on both the root path and `/v1` (preferred).

## Authentication

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/auth/register` | Create a user. Returns 409 if the username is taken. |
| `POST` | `/auth/login` | Returns `{access_token, token_type}`. |
| `GET`  | `/auth/me` | Returns `{username, documents}` for the current token. |
| `POST` | `/auth/refresh` | Returns a fresh `access_token`. |
| `POST` | `/auth/logout` | Clears the caller's conversation history. |

## Documents

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/upload` | Multipart `file=<pdf>`. Returns the document id. |
| `GET`  | `/documents` | `?page=&page_size=&search=&sort=`. Owner-scoped. |
| `GET`  | `/documents/{document_id}` | Returns detail plus a few sample chunks. |
| `DELETE` | `/documents/{document_id}` | 403 if the caller is not the owner. |
| `POST` | `/documents/bulk-delete` | Body: `{document_ids: [...]}`. |
| `GET`  | `/documents/{document_id}/history` | Returns prior chat turns. |
| `DELETE` | `/documents/{document_id}/history` | Clears the conversation. |

## Chat

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/chat` | `{document_id, question, top_k?}`. Returns answer + retrieved chunks. |
| `POST` | `/chat/stream` | Same body. Returns Server-Sent Events. |

## Health

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/health` | Reports the active LLM backend and number of loaded documents. |
| `GET` | `/ready` | Cheap liveness/readiness probe — no ML side effects. |

## Errors

Errors are returned as:

```json
{ "error_code": "document_not_found", "message": "Document 'abc' not found" }
```

| `error_code` | HTTP | Meaning |
| --- | --- | --- |
| `document_not_found` | 404 | The document id is unknown. |
| `invalid_credentials` | 401 | Bad username/password. |
| `username_exists` | 409 | Registration conflict. |
| `upload_too_large` | 413 | Body exceeds `MAX_UPLOAD_SIZE_MB`. |
| `empty_pdf` | 422 | No text could be extracted. |
| `internal_error` | 500 | Unhandled server error. |
