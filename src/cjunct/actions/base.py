"""Everything related to a default action interpretation"""

from __future__ import annotations

import asyncio
import typing as t
from dataclasses import dataclass, field
import enum

__all__ = [
    "ActionDependency",
    "ActionBase",
    "ActionStatus",
    "ActionSkip",
]

AT = t.TypeVar("AT", bound="ActionBase")
RT = t.TypeVar("RT")


class ActionSkip(BaseException):
    """Stop executing action"""


class ActionStatus(enum.Enum):
    """Action valid states"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    SKIPPED = "SKIPPED"

    def __repr__(self) -> str:
        return self.name


@dataclass
class ActionDependency:
    """Dependency info holder"""

    strict: bool = False
    external: bool = False


EventType = str


@dataclass
class ActionBase(t.Generic[RT]):
    """Base class for all actions"""

    name: str
    # Maybe add: type: str
    on_fail: t.Optional[str] = field(default=None, repr=False)
    visible: bool = field(default=True, repr=False)
    ancestors: t.Dict[str, ActionDependency] = field(default_factory=dict, repr=False)
    description: t.Optional[str] = None
    descendants: t.Dict[str, ActionDependency] = field(init=False, default_factory=dict, repr=False)
    tier: t.Optional[int] = field(init=False, default=None, repr=False)
    _status: ActionStatus = field(init=False, repr=False, default=ActionStatus.PENDING)
    # Do not create Future and Queue on constructing object to decouple from the event loop
    _maybe_finish_flag: t.Optional[asyncio.Future] = field(init=False, default=None, repr=False)
    _maybe_event_queue: t.Optional[asyncio.Queue[EventType]] = field(init=False, default=None, repr=False)
    _running_task: t.Optional[asyncio.Task] = field(init=False, default=None, repr=False)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, status={self._status.value})"

    def get_future(self) -> asyncio.Future:
        """Return a Future object indicating the end of the action"""
        if self._maybe_finish_flag is None:
            self._maybe_finish_flag = asyncio.get_event_loop().create_future()
        return self._maybe_finish_flag

    @property
    def _event_queue(self) -> asyncio.Queue[EventType]:
        if self._maybe_event_queue is None:
            self._maybe_event_queue = asyncio.Queue()
        return self._maybe_event_queue

    @property
    def status(self) -> ActionStatus:
        """Public getter"""
        return self._status

    async def run(self) -> RT:
        """Main entry to be implemented in subclasses"""
        raise NotImplementedError

    async def _await(self) -> t.Optional[RT]:
        fut = self.get_future()
        if fut.done():
            return fut.result()
        # Allocate asyncio task
        if self._running_task is None:
            self._running_task = asyncio.create_task(self.run())
            self._status = ActionStatus.RUNNING
        run_result: t.Optional[RT]
        try:
            run_result = await self._running_task
        except ActionSkip:
            run_result = None
        except Exception as e:
            self._status = ActionStatus.FAILURE
            if not fut.done():
                fut.set_exception(e)
            raise
        else:
            self._status = ActionStatus.SUCCESS
        if not fut.done():
            fut.set_result(run_result)
        return run_result

    def emit(self, message: EventType) -> None:
        """Issue a message"""
        self._event_queue.put_nowait(message)

    def skip(self) -> t.NoReturn:
        """Set status to SKIPPED"""
        self._status = ActionStatus.SKIPPED
        raise ActionSkip

    async def read_events(self) -> t.AsyncGenerator[EventType, None]:
        """Obtain all emitted events sequentially"""
        while True:
            # Wait for either an event or action finish
            queue_getter = asyncio.create_task(self._event_queue.get())
            await asyncio.wait(
                [self.get_future(), queue_getter],
                return_when=asyncio.FIRST_COMPLETED,
            )
            if queue_getter.done():
                yield queue_getter.result()
            if self.done():
                # The action is done, so we should drain the queue.
                # Prevent queue from async get since then.
                queue_getter.cancel()
                while True:
                    try:
                        yield self._event_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                return

    def __await__(self) -> t.Generator[t.Any, None, t.Optional[RT]]:
        return self._await().__await__()  # pylint: disable=no-member

    def done(self) -> bool:
        """Indicate whether the action is over"""
        return self.get_future().done() or self._status == ActionStatus.SKIPPED
