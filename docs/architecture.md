# Architecture

This is a small, single-process FastAPI service. The interesting parts
are the upload pipeline and the retrieval-augmented chat path.

## Module layout

```
app/
├── api/                # HTTP layer (FastAPI routers)
├── auth/               # JWT auth helpers + in-memory user store
├── middleware/         # Request ID, access log, rate limiter
├── models/             # Pydantic schemas (request/response shapes)
├── services/           # Business logic
│   ├── embedding_service.py   # sentence-transformers wrapper
│   ├── llm_service.py         # OpenAI + mock backends
│   ├── pdf_service.py         # PDF text extraction + chunking
│   ├── rag_service.py         # Upload pipeline + question answering
│   └── vector_store.py        # FAISS index + on-disk persistence
├── utils/              # Generic helpers (retry)
├── config.py           # pydantic-settings: env-driven config
├── constants.py        # Centralized tunables and string literals
├── exceptions.py       # Typed AppError hierarchy
├── error_handlers.py   # FastAPI global handlers
└── main.py             # FastAPI app construction
```

## Upload pipeline

```
PDF bytes
   │
   ▼
extract_text  ──►  list[(page, text)]
   │
   ▼
chunk_text    ──►  list[TextChunk]
   │
   ▼
embed_texts   ──►  np.ndarray[n, dim]
   │
   ▼
VectorStore.add_document  ──►  FAISS index + metadata.json on disk
```

## Chat pipeline

```
question
   │
   ▼
embed_query  ──►  np.ndarray[1, dim]
   │
   ▼
DocumentIndex.search(top_k)  ──►  list[(chunk, score)]
   │
   ▼
build prompt with context  ──►  str
   │
   ▼
LLMBackend.generate  ──►  answer
```

## Persistence

Each document lives in its own directory under `FAISS_PERSIST_DIR`:

```
faiss_indexes/
└── <document_id>/
    ├── index.faiss      # the FAISS index
    └── metadata.json    # filename, owner, created_at, chunks
```

The vector store is rebuilt from disk on startup.

## Ownership

Every document is tagged with the username of the uploader. The list,
chat, and delete routes check ownership and return 403 for non-owners.
Legacy documents that predate the ownership change have a `null` owner
and remain accessible to anyone.

## Conversation memory

A small in-memory `ConversationStore` keeps a bounded ring of recent
`(question, answer)` turns per `(user, document_id)` pair. It is cleared
on `/auth/logout` and on `DELETE /documents/{id}/history`. The store is
non-persistent by design — long-term chat history would require a
dedicated table that we have not yet justified.
