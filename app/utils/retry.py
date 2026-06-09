"""Simple async retry helper with exponential backoff and jitter.

Tailored for transient errors talking to upstream LLM providers. We do not
retry programming errors (e.g. invalid request payloads), only the
exceptions the caller explicitly opts into.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    on_giveup: Callable[[BaseException], None] | None = None,
) -> T:
    """Run *fn* up to *attempts* times with exponential backoff + jitter."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    if base_delay < 0 or max_delay < 0:
        raise ValueError("delays must be non-negative")
    last_exc: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except retry_on as exc:
            last_exc = exc
            if attempt == attempts:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0, base_delay)
            logger.warning(
                "Attempt %d/%d failed (%s); retrying in %.2fs",
                attempt,
                attempts,
                type(exc).__name__,
                delay,
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    if on_giveup is not None:
        on_giveup(last_exc)
    raise last_exc
