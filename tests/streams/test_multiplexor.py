import asyncio
import random
import typing as t

import pytest

from cjunct.streams.multiplexor import AsyncMultiplexor


@pytest.mark.asyncio
async def test_simple_join():
    """Validate the simplest join of two string emitters"""
    results: t.Set[str] = set()

    async def counter(span: int) -> t.AsyncGenerator[str, None]:
        for i in range(span):
            await asyncio.sleep(random.uniform(0, 0.01))
            yield f"{i + 1}/{span}"

    async with AsyncMultiplexor() as plex:
        plex.attach(counter(1))
        plex.attach(counter(2))

        async def breaker():
            while plex.status != "idle":
                await asyncio.sleep(0.01)
            plex.stop()

        breaker_task = asyncio.create_task(breaker())
        async for item in plex:
            results.add(item)
        await breaker_task
        assert results == {"1/1", "1/2", "2/2"}
