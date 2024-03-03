"""Everything related to a default action interpretation"""

from __future__ import annotations

import asyncio
import enum
import typing as t
from dataclasses import dataclass

import classlogging

from ..results import ResultsProxy, ActionResultDataType

__all__ = [
    "ActionDependency",
    "ActionBase",
    "ActionStatus",
    "ActionSkip",
    "Stderr",
    "ArgsBase",
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

    __str__ = __repr__


@dataclass
class ActionDependency:
    """Dependency info holder"""

    strict: bool = False
    external: bool = False


EventType = str


class Stderr(str):
    """Strings related to standard error stream"""


@dataclass
class ArgsBase:
    """Default empty args holder.
    Should be subclassed and then added to the `args` annotation of any action class."""


class ActionBase(t.Generic[RT], classlogging.LoggerMixin):
    """Base class for all actions"""

    args: ArgsBase

    def __init__(
        self,
        name: str,
        args: ArgsBase = ArgsBase(),
        on_fail: t.Optional[str] = None,
        visible: bool = True,
        ancestors: t.Optional[t.Dict[str, ActionDependency]] = None,
        description: t.Optional[str] = None,
    ) -> None:
        self.name: str = name
        self.args: ArgsBase = args
        self.on_fail: t.Optional[str] = on_fail
        self.visible: bool = visible
        self.description: t.Optional[str] = description
        self.ancestors: t.Dict[str, ActionDependency] = ancestors or {}

        self.result: t.Dict[str, str] = {}
        self._status: ActionStatus = ActionStatus.PENDING
        # Do not create asyncio-related objects on constructing object to decouple from the event loop
        self._maybe_finish_flag: t.Optional[asyncio.Future] = None
        self._maybe_event_queue: t.Optional[asyncio.Queue[EventType]] = None
        self._running_task: t.Optional[asyncio.Task] = None

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

    async def _await(self) -> ActionResultDataType:
        fut = self.get_future()
        if fut.done():
            return fut.result()
        # Allocate asyncio task
        if self._running_task is None:
            self.logger.info(f"Running action: {self.name!r}")
            self._running_task = asyncio.create_task(self.run())
            self._status = ActionStatus.RUNNING
        result: ActionResultDataType = {}
        try:
            running_task_result = await self._running_task
            if isinstance(running_task_result, t.Mapping):
                result.update(running_task_result)
            elif running_task_result is not None:
                self.logger.warning(
                    f"Action {self.name!r} returned something different from None "
                    f"or a mapping: {type(running_task_result)}"
                )
        except ActionSkip:
            pass
        except Exception as e:
            self.fail(e)
            raise
        else:
            self._status = ActionStatus.SUCCESS
        if not fut.done():
            fut.set_result(result)
        return result

    def emit(self, message: EventType) -> None:
        """Issue a message"""
        self._event_queue.put_nowait(message)

    def skip(self) -> t.NoReturn:
        """Set status to SKIPPED"""
        self._status = ActionStatus.SKIPPED
        self.logger.info(f"Action {self.name!r} skipped")
        raise ActionSkip

    def fail(self, exception: Exception) -> None:
        """Set corresponding error"""
        self._status = ActionStatus.FAILURE
        self.logger.info(f"Action {self.name!r} failed: {repr(exception)}")
        if not self.get_future().done():
            self.get_future().set_exception(exception)

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

    def __await__(self) -> t.Generator[t.Any, None, ActionResultDataType]:
        return self._await().__await__()  # pylint: disable=no-member

    def done(self) -> bool:
        """Indicate whether the action is over"""
        return self.get_future().done() or self._status == ActionStatus.SKIPPED

    async def warmup(self, results: ResultsProxy) -> None:
        """May adopt any result of completed tasks"""
