from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import tiktoken

from app.config import settings

logger = logging.getLogger(__name__)

RAG_PROMPT_TEMPLATE = """You are a document assistant.
Use ONLY the provided context to answer.
If the answer is not found in the context, say "I don't know based on the provided document."

Context:
{context}

Question:
{question}

Answer:"""


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens using tiktoken. Falls back to rough estimate."""
    try:
        enc = tiktoken.encoding_for_model(model)
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


class LLMBackend(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str) -> str: ...

    def build_prompt(self, context: str, question: str) -> str:
        return RAG_PROMPT_TEMPLATE.format(context=context, question=question)


class OpenAIBackend(LLMBackend):
    name: str = "openai"

    def __init__(self) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def generate(self, prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""


class MockBackend(LLMBackend):
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


# Singleton
llm_backend = get_llm_backend()
