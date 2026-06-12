from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import asyncio

import tiktoken

from app.config import settings
from app.constants import DEFAULT_LLM_MAX_TOKENS, DEFAULT_LLM_TEMPERATURE
from app.exceptions import AppError
from app.utils.retry import retry_async


class LLMError(AppError):
    error_code = "llm_error"
    status_code = 502


class LLMTimeoutError(LLMError):
    error_code = "llm_timeout"
    status_code = 504

logger = logging.getLogger(__name__)

RAG_PROMPT_WITH_HISTORY_TEMPLATE = """You are a document assistant.
Use ONLY the provided context to answer. If the answer is not in the
context, say "I don't know based on the provided document." Always cite
the page number you used in square brackets like [page 3].

Previous turns (most recent last):
{history}

Context:
{context}

Question:
{question}

Answer:"""


MAX_PROMPT_CHARS = 16_000  # rough guard before the model itself rejects


RAG_PROMPT_TEMPLATE = """You are a document assistant.
Use ONLY the provided context to answer.
If the answer is not found in the context, say "I don't know based on the provided document."
Always cite the page number you used in square brackets like [page 3].

Context:
{context}

Question:
{question}

Answer:"""


def _fallback_token_estimate(text: str) -> int:
    return max(1, len(text) // 4)


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens using tiktoken. Falls back to a rough character estimate.

    The fallback runs when the model is unknown or tiktoken fails to load
    the encoding. Using `len(text) // 4` keeps numbers in the right
    ballpark for English content without hard-blocking the request.
    """
    if not text:
        return 0
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        return _fallback_token_estimate(text)


class LLMBackend(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str: ...

    def supports_streaming(self) -> bool:
        return False

    def build_prompt(self, context: str, question: str) -> str:
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS]
        return prompt

    def build_prompt_with_history(
        self,
        context: str,
        question: str,
        history: list[tuple[str, str]],
    ) -> str:
        history_text = "\n".join(f"Q: {q}\nA: {a}" for q, a in history) or "(none)"
        prompt = RAG_PROMPT_WITH_HISTORY_TEMPLATE.format(
            context=context, question=question, history=history_text
        )
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS]
        return prompt


class OpenAIBackend(LLMBackend):
    name: str = "openai"

    def supports_streaming(self) -> bool:
        return True

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OpenAIBackend constructed without OPENAI_API_KEY")
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def generate(self, prompt: str) -> str:
        async def _call() -> str:
            try:
                response = await asyncio.wait_for(
                    self._client.chat.completions.create(
                        model=self._model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=DEFAULT_LLM_TEMPERATURE,
                        max_tokens=DEFAULT_LLM_MAX_TOKENS,
                    ),
                    timeout=settings.llm_request_timeout,
                )
            except asyncio.TimeoutError as e:
                raise LLMTimeoutError(
                    f"OpenAI call exceeded {settings.llm_request_timeout}s"
                ) from e
            return response.choices[0].message.content or ""

        try:
            return await retry_async(
                _call,
                attempts=3,
                base_delay=0.5,
                max_delay=4.0,
                retry_on=(Exception,),
            )
        except LLMTimeoutError:
            raise
        except Exception as e:
            raise LLMError(f"OpenAI call failed after retries: {e}") from e


class MockBackend(LLMBackend):
    """Deterministic backend used when no real provider is configured.

    The mock echoes a short notice and includes the question so tests can
    assert against a stable string. It is intentionally cheap and offline.
    """

    name: str = "mock"

    async def generate(self, prompt: str) -> str:
        return (
            "[Mock LLM] No OPENAI_API_KEY configured. "
            "Set OPENAI_API_KEY in your .env to enable real answers. "
            "The retrieved context chunks are still valid and shown below."
        )


def get_llm_backend() -> LLMBackend:
    if settings.openai_api_key:
        logger.info("Using OpenAI backend (%s)", settings.openai_model)
        return OpenAIBackend()
    logger.warning("No OPENAI_API_KEY found — using mock LLM backend")
    return MockBackend()


_backend: LLMBackend | None = None


def _resolve_backend() -> LLMBackend:
    global _backend
    if _backend is None:
        _backend = get_llm_backend()
    return _backend


class _BackendProxy:
    """Lazy proxy so importing this module does not eagerly construct a backend."""

    @property
    def name(self) -> str:
        return _resolve_backend().name

    def build_prompt(self, context: str, question: str) -> str:
        return _resolve_backend().build_prompt(context=context, question=question)

    def build_prompt_with_history(
        self,
        context: str,
        question: str,
        history: list[tuple[str, str]],
    ) -> str:
        return _resolve_backend().build_prompt_with_history(
            context=context, question=question, history=history
        )

    async def generate(self, prompt: str) -> str:
        return await _resolve_backend().generate(prompt)


# Public singleton — behaves like an LLMBackend but stays lazy.
llm_backend = _BackendProxy()
