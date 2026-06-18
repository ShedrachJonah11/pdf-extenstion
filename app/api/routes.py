import json
import logging
from typing import Dict

import faiss
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_owned_document
from app.auth.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    register_user,
)
from app.config import settings
from app.constants import (
    DEFAULT_SAMPLE_CHUNKS,
    DOCUMENT_SORT_KEYS,
    MAX_SAMPLE_CHUNKS,
    PDF_CONTENT_TYPES,
    PDF_EXTENSION,
    SAMPLE_CHUNK_PREVIEW_CHARS,
)
from app.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    ForbiddenError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
)
from app.middleware.rate_limiter import limiter
from app.models.schemas import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    ChatRequest,
    ChatResponse,
    ChunkPreview,
    ConversationHistoryResponse,
    ConversationTurn,
    DocumentDetail,
    DocumentInfo,
    DocumentListResponse,
    HealthResponse,
    Token,
    UploadResponse,
    UserCreate,
)
from app.services.conversation import Turn, conversation_store
from app.services.embedding_service import embed_query
from app.services.llm_service import llm_backend
from app.services.rag_service import ask_question, process_upload
from app.services.vector_store import vector_store
from app.utils.pagination import slice_page, validate_page_params

logger = logging.getLogger(__name__)

router = APIRouter()
documents_router = APIRouter(prefix="/documents", tags=["documents"])
chat_router = APIRouter(tags=["chat"])
health_router = APIRouter(tags=["health"])


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    import time

    from app import __version__
    from app.auth.auth import user_count

    return HealthResponse(
        llm_backend=llm_backend.name,
        documents_loaded=vector_store.document_count,
        version=__version__,
        uptime_seconds=round(time.monotonic() - _START_MONOTONIC, 3),
        users_registered=user_count(),
    )


@router.get("/ready", tags=["health"])
async def ready() -> Dict[str, bool]:
    """Liveness/readiness probe — does not load the embedding model."""
    return {"ready": True}


import time as _time  # local import to keep the public namespace clean
_START_MONOTONIC = _time.monotonic()


# ── Auth ──────────────────────────────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=None)
async def register(body: UserCreate) -> Dict[str, str]:
    try:
        register_user(body.username, body.password)
    except UsernameAlreadyExistsError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {"message": f"User '{body.username}' registered"}


@auth_router.post("/login", response_model=Token)
async def login(body: UserCreate) -> Token:
    if not authenticate_user(body.username, body.password):
        raise InvalidCredentialsError("Invalid credentials")
    token = create_access_token(body.username)
    return Token(access_token=token)


@auth_router.get("/me")
async def me(user: str = Depends(get_current_user)) -> Dict[str, object]:
    return {
        "username": user,
        "documents": vector_store.count_for(user),
        "total_chunks": vector_store.total_chunks_for(user),
    }


@auth_router.post("/refresh", response_model=Token)
async def refresh(user: str = Depends(get_current_user)) -> Token:
    return Token(access_token=create_access_token(user))


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: str = Depends(get_current_user)) -> None:
    # JWTs are stateless — there is no server-side token revocation. We
    # still clear the user's in-memory conversation history so the next
    # session starts clean.
    conversation_store.clear_for_user(user)


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
@limiter.limit(settings.rate_limit)
async def upload_pdf(
    request: Request,
    file: UploadFile,
    user: str = Depends(get_current_user),
) -> UploadResponse:
    # Validate content type
    if file.content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted",
        )

    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(PDF_EXTENSION):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File must have .pdf extension",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty",
        )

    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Body does not look like a PDF (missing %PDF- header)",
        )

    logger.info(
        "Upload accepted: filename=%s, size=%d bytes, user=%s",
        filename,
        len(contents),
        user,
    )

    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb}MB limit",
        )

    try:
        result = await process_upload(filename, contents, owner=user)
    except DocumentProcessingError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception:
        logger.exception("Upload processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF",
        )

    return result


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse, tags=["chat"])
@limiter.limit(settings.rate_limit)
async def chat(
    request: Request,
    body: ChatRequest,
    user: str = Depends(get_current_user),
) -> ChatResponse:
    doc = vector_store.get(body.document_id)
    if doc is not None and doc.owner is not None and doc.owner != user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this document",
        )
    prior = conversation_store.get_turns(user, body.document_id)
    history_pairs = [(t.question, t.answer) for t in prior]
    try:
        response = await ask_question(
            body.document_id,
            body.question,
            top_k=body.top_k,
            history=history_pairs,
        )
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception:
        logger.exception("Chat failed for document %s", body.document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer",
        )

    conversation_store.append_turn(
        user, body.document_id, Turn(question=body.question, answer=response.answer)
    )
    return response


# ── Chat Streaming ───────────────────────────────────────────────────────────

@router.post("/chat/stream", response_model=None, tags=["chat"])
@limiter.limit(settings.rate_limit)
async def chat_stream(
    request: Request,
    body: ChatRequest,
    user: str = Depends(get_current_user),
) -> StreamingResponse:
    """Stream the answer token-by-token (SSE). Falls back to single chunk for mock backend."""
    doc_index = vector_store.get(body.document_id)
    if doc_index is None:
        raise HTTPException(status_code=404, detail=f"Document '{body.document_id}' not found")
    if doc_index.owner is not None and doc_index.owner != user:
        raise HTTPException(status_code=403, detail="You do not own this document")

    query_emb = embed_query(body.question)
    faiss.normalize_L2(query_emb)
    results = doc_index.search(query_emb, top_k=body.top_k)

    context = "\n\n---\n\n".join(f"[Page {c.page}] {c.text}" for c, _ in results)
    prompt = llm_backend.build_prompt(context=context, question=body.question)

    chunks_data = [
        {"text": c.text, "page": c.page, "chunk_index": c.chunk_index, "score": round(s, 4)}
        for c, s in results
    ]

    async def event_stream():
        # Send retrieved chunks first
        yield f"data: {json.dumps({'type': 'chunks', 'chunks': chunks_data})}\n\n"

        backend_supports_stream = getattr(llm_backend, "supports_streaming", lambda: False)()
        if backend_supports_stream:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            stream = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
        else:
            answer = await llm_backend.generate(prompt)
            yield f"data: {json.dumps({'type': 'token', 'content': answer})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Documents ─────────────────────────────────────────────────────────────────

@router.get("/documents", response_model=DocumentListResponse, tags=["documents"])
async def list_documents(
    user: str = Depends(get_current_user),
    page: int = 1,
    page_size: int = 50,
    search: str | None = None,
    sort: str = "created_at",
) -> DocumentListResponse:
    try:
        page_params = validate_page_params(page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if search:
        docs = vector_store.find_by_filename(user, search)
    else:
        docs = vector_store.list_documents(owner=user)

    if sort not in DOCUMENT_SORT_KEYS:
        raise HTTPException(
            status_code=422,
            detail=f"sort must be one of: {', '.join(DOCUMENT_SORT_KEYS)}",
        )
    if sort == "filename":
        docs.sort(key=lambda d: d.filename.lower())
    else:
        docs.sort(key=lambda d: d.created_at or "", reverse=True)
    total = len(docs)
    page_docs = slice_page(docs, page_params)

    return DocumentListResponse(
        documents=[
            DocumentInfo(
                document_id=d.document_id,
                filename=d.filename,
                total_pages=d.total_pages,
                total_chunks=len(d.chunks),
                owner=d.owner,
                created_at=d.created_at,
            )
            for d in page_docs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/documents/{document_id}", response_model=DocumentDetail, tags=["documents"])
async def get_document(
    samples: int = DEFAULT_SAMPLE_CHUNKS,
    doc=Depends(get_owned_document),
) -> DocumentDetail:
    sample_count = max(0, min(samples, MAX_SAMPLE_CHUNKS, len(doc.chunks)))
    from app.utils.text import truncate

    return DocumentDetail(
        document_id=doc.document_id,
        filename=doc.filename,
        total_pages=doc.total_pages,
        total_chunks=len(doc.chunks),
        owner=doc.owner,
        created_at=doc.created_at,
        sample_chunks=[
            ChunkPreview(
                chunk_index=c.chunk_index,
                page=c.page,
                text=truncate(c.text, SAMPLE_CHUNK_PREVIEW_CHARS),
            )
            for c in doc.chunks[:sample_count]
        ],
    )


@router.post("/documents/bulk-delete", response_model=BulkDeleteResponse, tags=["documents"])
async def bulk_delete_documents(
    body: BulkDeleteRequest,
    user: str = Depends(get_current_user),
) -> BulkDeleteResponse:
    deleted = 0
    not_found: list[str] = []
    forbidden: list[str] = []
    for doc_id in body.document_ids:
        doc = vector_store.get(doc_id)
        if doc is None:
            not_found.append(doc_id)
            continue
        if doc.owner is not None and doc.owner != user:
            forbidden.append(doc_id)
            continue
        if vector_store.delete(doc_id):
            deleted += 1
    return BulkDeleteResponse(deleted=deleted, not_found=not_found, forbidden=forbidden)


@router.get(
    "/documents/{document_id}/history",
    response_model=ConversationHistoryResponse,
    tags=["chat"],
)
async def get_conversation_history(
    document_id: str,
    user: str = Depends(get_current_user),
) -> ConversationHistoryResponse:
    doc = vector_store.get(document_id)
    if doc is not None and doc.owner is not None and doc.owner != user:
        raise HTTPException(status_code=403, detail="You do not own this document")
    turns = conversation_store.get_turns(user, document_id)
    return ConversationHistoryResponse(
        document_id=document_id,
        turns=[ConversationTurn(question=t.question, answer=t.answer) for t in turns],
        total=len(turns),
    )


@router.delete(
    "/documents/{document_id}/history",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["chat"],
)
async def clear_conversation_history(
    document_id: str,
    user: str = Depends(get_current_user),
) -> None:
    conversation_store.clear(user, document_id)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["documents"],
)
async def delete_document(
    document_id: str,
    user: str = Depends(get_current_user),
) -> None:
    doc = vector_store.get(document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.owner is not None and doc.owner != user:
        raise ForbiddenError("You do not own this document")
    vector_store.delete(document_id)
