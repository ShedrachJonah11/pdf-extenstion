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

from app.auth.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    register_user,
)
from app.config import settings
from app.middleware.rate_limiter import limiter
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    DocumentListResponse,
    HealthResponse,
    Token,
    UploadResponse,
    UserCreate,
)
from app.services.embedding_service import embed_query
from app.services.llm_service import llm_backend
from app.services.rag_service import ask_question, process_upload
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        llm_backend=llm_backend.name,
        documents_loaded=vector_store.document_count,
    )


# ── Auth ──────────────────────────────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=None)
async def register(body: UserCreate) -> Dict[str, str]:
    try:
        register_user(body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return {"message": f"User '{body.username}' registered"}


@auth_router.post("/login", response_model=Token)
async def login(body: UserCreate) -> Token:
    if not authenticate_user(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(body.username)
    return Token(access_token=token)


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit)
async def upload_pdf(
    request: Request,
    file: UploadFile,
    _user: str = Depends(get_current_user),
) -> UploadResponse:
    # Validate content type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted",
        )

    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File must have .pdf extension",
        )

    contents = await file.read()

    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb}MB limit",
        )

    try:
        result = await process_upload(filename, contents)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        logger.exception("Upload processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process PDF",
        )

    return result


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.rate_limit)
async def chat(
    request: Request,
    body: ChatRequest,
    _user: str = Depends(get_current_user),
) -> ChatResponse:
    try:
        return await ask_question(body.document_id, body.question)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        logger.exception("Chat failed for document %s", body.document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer",
        )


# ── Chat Streaming ───────────────────────────────────────────────────────────

@router.post("/chat/stream", response_model=None)
@limiter.limit(settings.rate_limit)
async def chat_stream(
    request: Request,
    body: ChatRequest,
    _user: str = Depends(get_current_user),
) -> StreamingResponse:
    """Stream the answer token-by-token (SSE). Falls back to single chunk for mock backend."""
    doc_index = vector_store.get(body.document_id)
    if doc_index is None:
        raise HTTPException(status_code=404, detail=f"Document '{body.document_id}' not found")

    query_emb = embed_query(body.question)
    faiss.normalize_L2(query_emb)
    results = doc_index.search(query_emb, top_k=5)

    context = "\n\n---\n\n".join(f"[Page {c.page}] {c.text}" for c, _ in results)
    prompt = llm_backend.build_prompt(context=context, question=body.question)

    chunks_data = [
        {"text": c.text, "page": c.page, "chunk_index": c.chunk_index, "score": round(s, 4)}
        for c, s in results
    ]

    async def event_stream():
        # Send retrieved chunks first
        yield f"data: {json.dumps({'type': 'chunks', 'chunks': chunks_data})}\n\n"

        if llm_backend.name == "openai":
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

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    _user: str = Depends(get_current_user),
) -> DocumentListResponse:
    docs = vector_store.list_documents()
    return DocumentListResponse(
        documents=[
            DocumentInfo(
                document_id=d.document_id,
                filename=d.filename,
                total_pages=d.total_pages,
                total_chunks=len(d.chunks),
            )
            for d in docs
        ],
        total=len(docs),
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    _user: str = Depends(get_current_user),
) -> None:
    if not vector_store.delete(document_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
