from __future__ import annotations

import asyncio
import typing as t
import uuid

from classlogging import LoggerMixin

GT = t.TypeVar("GT")
MT = t.TypeVar("MT", bound="AsyncMultiplexor")

__all__ = [
    "AsyncMultiplexor",
]


class AsyncMultiplexor(t.Generic[GT], LoggerMixin):
    """Multiplexor object for async streams"""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._getter: asyncio.Task | None = None
        self._running: bool = False
        self._reader_tasks: dict[uuid.UUID, asyncio.Task] = {}

    async def __aenter__(self: MT) -> MT:
        self._running = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.stop()
        return exc_type is None

    def __aiter__(self: MT) -> MT:
        return self

    async def __anext__(self) -> GT:
        if not self._running:
            raise StopAsyncIteration
        self.logger.trace(f"Launching tick for {self!r}")
        self._getter = asyncio.create_task(
            coro=self._queue.get(),
            name=f"{self!r} tick",
        )
        try:
            return await self._getter
        except asyncio.CancelledError as e:
            raise StopAsyncIteration from e
        finally:
            self._getter = None

    def stop(self) -> None:
        """Prevent further multiplexing and stop active reading"""
        for reader_task in self._reader_tasks.values():
            reader_task.cancel()
        self._reader_tasks = {}
        if self._getter is not None:
            self._getter.cancel()
        self._running = False

    async def _source_reader(self, uid: uuid.UUID, source: t.AsyncIterable[GT]):
        try:
            async for item in source:
                await self._queue.put(item)
        finally:
            if uid in self._reader_tasks:
                self._reader_tasks.pop(uid).cancel()

    def attach(self, source: t.AsyncIterable[GT]) -> asyncio.Task:
        """Add yet another emitter.
        :param source: async-iterable object to exhaust
        :return: asyncio.Task object for possible source reading cancellation"""
        task_uid = uuid.uuid4()
        self.logger.trace(f"Launching reader {source!r} for {self!r}")
        reader_task = asyncio.create_task(
            coro=self._source_reader(uid=task_uid, source=source),
            name=f"{self!r} source reader {task_uid}",
        )
        self._reader_tasks[task_uid] = reader_task
        return reader_task
