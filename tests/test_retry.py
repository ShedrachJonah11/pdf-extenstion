import pytest

from app.utils.retry import retry_async


@pytest.mark.asyncio
async def test_returns_first_success_without_retry() -> None:
    calls = 0

    async def fn() -> int:
        nonlocal calls
        calls += 1
        return 42

    assert await retry_async(fn, attempts=3, base_delay=0) == 42
    assert calls == 1


@pytest.mark.asyncio
async def test_retries_on_transient_failure() -> None:
    calls = 0

    async def fn() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise RuntimeError("boom")
        return "ok"

    assert await retry_async(fn, attempts=5, base_delay=0) == "ok"
    assert calls == 3


@pytest.mark.asyncio
async def test_raises_after_all_attempts_exhausted() -> None:
    async def fn() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        await retry_async(fn, attempts=2, base_delay=0)


@pytest.mark.asyncio
async def test_does_not_retry_unexpected_exception_types() -> None:
    calls = 0

    async def fn() -> None:
        nonlocal calls
        calls += 1
        raise KeyError("not transient")

    with pytest.raises(KeyError):
        await retry_async(fn, attempts=3, base_delay=0, retry_on=(ValueError,))
    assert calls == 1


@pytest.mark.asyncio
async def test_rejects_zero_attempts() -> None:
    async def fn() -> int:
        return 1
    with pytest.raises(ValueError):
        await retry_async(fn, attempts=0)


@pytest.mark.asyncio
async def test_rejects_negative_delay() -> None:
    async def fn() -> int:
        return 1
    with pytest.raises(ValueError):
        await retry_async(fn, attempts=2, base_delay=-1)


@pytest.mark.asyncio
async def test_on_giveup_fires_with_last_exception() -> None:
    seen: list[BaseException] = []

    async def fn() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await retry_async(fn, attempts=2, base_delay=0, on_giveup=seen.append)
    assert len(seen) == 1
    assert isinstance(seen[0], RuntimeError)
