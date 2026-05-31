# Data model

This is a small service so the data model is intentionally simple. Both
the user store and the document store are in-process; only the FAISS
index and its metadata live on disk.

## User

| field | type | notes |
| --- | --- | --- |
| `username` | str | 3–50 chars, `[a-zA-Z0-9._-]` only |
| `hashed_password` | str | bcrypt |

In-memory map `{username: hashed_password}`. Resets on restart.

## DocumentIndex

In-memory representation, persisted as `metadata.json` next to the FAISS
file.

| field | type | notes |
| --- | --- | --- |
| `document_id` | str | 16-char hex from `uuid4().hex[:16]` |
| `filename` | str | uploaded filename |
| `total_pages` | int | from the source PDF |
| `chunks` | list\[TextChunk\] | `text`, `page`, `chunk_index` |
| `owner` | str \| null | uploader's username, or null for legacy docs |
| `created_at` | str | ISO 8601 in UTC |

## TextChunk

| field | type | notes |
| --- | --- | --- |
| `text` | str | normalized whitespace; no control chars |
| `page` | int | 1-indexed |
| `chunk_index` | int | monotonically increasing within a document |

## Conversation history

| field | type | notes |
| --- | --- | --- |
| `(user, document_id)` | tuple key | scope |
| `turns` | deque[Turn] | bounded by `MAX_TURNS_PER_KEY` |

Both `Turn.question` and `Turn.answer` are plain strings.
