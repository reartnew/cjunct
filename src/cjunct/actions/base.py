"""Everything related to a default action interpretation"""

from __future__ import annotations

import asyncio
import base64
import enum
import re
import textwrap
import typing as t
from dataclasses import dataclass, fields

import classlogging

from .constants import ACTION_RESERVED_FIELD_NAMES
from .types import Stderr, EventType, OutcomeStorageType
from ..exceptions import ActionRunError

__all__ = [
    "ActionDependency",
    "ActionBase",
    "ActionStatus",
    "ActionSkip",
    "ArgsBase",
    "EmissionScannerActionBase",
]


class ActionSkip(BaseException):
    """Stop executing action"""


class ActionStatus(enum.Enum):
    """Action valid states"""

    PENDING = "PENDING"  # Enabled, but not started yet
    RUNNING = "RUNNING"  # Execution in process
    SUCCESS = "SUCCESS"  # Finished without errors
    FAILURE = "FAILURE"  # Erroneous action
    SKIPPED = "SKIPPED"  # May be set by action itself
    OMITTED = "OMITTED"  # Disabled during interaction or via checklists

    def __repr__(self) -> str:
        return self.name

    __str__ = __repr__


@dataclass
class ActionDependency:
    """Dependency info holder"""

    strict: bool = False
    external: bool = False


class ArgsMeta(type):
    """Metaclass for args containers that makes them all dataclasses"""

    def __new__(cls, name, bases, dct):
        sub_dataclass = dataclass(super().__new__(cls, name, bases, dct))
        reserved_names_collisions: t.Set[str] = {f.name for f in fields(sub_dataclass)} & ACTION_RESERVED_FIELD_NAMES
        if reserved_names_collisions:
            raise TypeError(f"Reserved names found in {name!r} class definition: {sorted(reserved_names_collisions)}")
        return sub_dataclass


@dataclass
class ArgsBase(metaclass=ArgsMeta):
    """Default empty args holder.
    Should be subclassed and then added to the `args` annotation of any action class."""


class ActionBase(classlogging.LoggerMixin):
    """Base class for all actions"""

    args: ArgsBase

    def __init__(
        self,
        name: str,
        args: ArgsBase = ArgsBase(),
        ancestors: t.Optional[t.Dict[str, ActionDependency]] = None,
        description: t.Optional[str] = None,
        selectable: bool = True,
    ) -> None:
        self.name: str = name
        self.args: ArgsBase = args
        self.description: t.Optional[str] = description
        self.ancestors: t.Dict[str, ActionDependency] = ancestors or {}
        self.selectable: bool = selectable

        self._yielded_keys: OutcomeStorageType = {}
        self._status: ActionStatus = ActionStatus.PENDING
        # Do not create asyncio-related objects on constructing object to decouple from the event loop
        self._maybe_finish_flag: t.Optional[asyncio.Future] = None
        self._maybe_event_queue: t.Optional[asyncio.Queue[EventType]] = None
        self._running_task: t.Optional[asyncio.Task] = None

    @property
    def enabled(self) -> bool:
        """Check whether the action has not been disabled"""
        return self._status != ActionStatus.OMITTED

    def disable(self) -> None:
        """Marking the action as not planned for launch"""
        self.logger.info(f"Disabling {self}")
        if self._status != ActionStatus.PENDING:
            raise RuntimeError(f"Action {self.name} can't be disabled due to its status: {self._status!r}")
        self._status = ActionStatus.OMITTED
        self.get_future().set_result(None)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, status={self._status.value})"

    def yield_outcome(self, key: str, value: t.Any) -> None:
        """Report outcome key"""
        self.logger.info(f"Yielded a key: {key!r}")
        self._yielded_keys[key] = value

    def get_outcomes(self) -> OutcomeStorageType:
        """Report all registered outcomes"""
        return self._yielded_keys

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

    async def run(self) -> None:
        """Main entry to be implemented in subclasses"""
        raise NotImplementedError

    async def _run_with_log_context(self) -> None:
        with self.logger.context(name=self.name):
            self.logger.info("Running action")
            return await self.run()

    async def _await(self) -> None:
        fut = self.get_future()
        if fut.done():
            return fut.result()
        # Allocate asyncio task
        if self._running_task is None:
            self._running_task = asyncio.create_task(self._run_with_log_context())
            self._status = ActionStatus.RUNNING
        try:
            if (running_task_result := await self._running_task) is not None:
                self.logger.warning(f"Action {self.name!r} return type is {type(running_task_result)} (not NoneType)")
        except ActionSkip:
            pass
        except ActionRunError:
            raise
        except Exception as e:
            self._internal_fail(e)
            raise
        else:
            self._status = ActionStatus.SUCCESS
        if not fut.done():
            fut.set_result(None)

    def emit(self, message: EventType) -> None:
        """Issue a message"""
        self._event_queue.put_nowait(message)

    def skip(self) -> t.NoReturn:
        """Set status to SKIPPED and stop execution"""
        self._internal_skip()
        raise ActionSkip

    def _internal_skip(self) -> None:
        self._status = ActionStatus.SKIPPED
        self.logger.info(f"Action {self.name!r} skipped")

    def fail(self, message: str) -> t.NoReturn:
        """Set corresponding error message and raise an exception"""
        exception = ActionRunError(message)
        self._internal_fail(exception)
        raise exception

    def _internal_fail(self, exception: Exception) -> None:
        if not self.get_future().done():
            self._status = ActionStatus.FAILURE
            self.logger.info(f"Action {self.name!r} failed: {repr(exception)}")
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

    def __await__(self) -> t.Generator[t.Any, None, None]:
        return self._await().__await__()  # pylint: disable=no-member

    def done(self) -> bool:
        """Indicate whether the action is over"""
        return self.get_future().done() or self._status in (ActionStatus.SKIPPED, ActionStatus.OMITTED)


# pylint: disable=abstract-method
class EmissionScannerActionBase(ActionBase):
    """Base class for stream-scanning actions"""

    _YIELD_SCAN_PATTERN: t.ClassVar[t.Pattern] = re.compile(r"^(.*?)##cjunct\[yield-outcome-b64\s*(\S+)\s+(\S*)\s*]##$")
    _YIELD_SHELL_FUNCTION_DEFINITION: str = textwrap.dedent(
        r"""
            yield_outcome(){
              [ "$1" = "" ] && echo "Missing key (first argument)" && return 1
              command -v base64 >/dev/null || ( echo "Missing command: base64" && return 2 )
              [ "$2" = "" ] && value="$(cat /dev/stdin)" || value="$2"
              echo "##cjunct[yield-outcome-b64 $(
                printf "$1" | base64 | tr -d '\n'
              ) $(
                printf "$value" | base64 | tr -d '\n'
              )]##"
              return 0
            }
        """
    ).lstrip()

    def emit(self, message: EventType) -> None:
        # Do not check stderr
        if isinstance(message, Stderr):
            super().emit(message)
            return
        memorized_prefix: str = ""
        for line in message.splitlines():
            # `endswith` is a cheaper check than re.findall
            if line.endswith("]##") and (matches := self._YIELD_SCAN_PATTERN.findall(line)):
                try:
                    for preceding_content, encoded_key, encoded_value in matches:
                        memorized_prefix += preceding_content
                        self.logger.debug(f"Action {self.name!r} emission stream reported an outcome: {encoded_key!r}")
                        key: str = base64.b64decode(encoded_key, validate=True).decode()
                        value: str = base64.b64decode(encoded_value, validate=True).decode()
                        self.yield_outcome(key, value)
                except Exception:
                    self.logger.warning("Failed while parsing system message", exc_info=True)
            else:
                super().emit(memorized_prefix + line)
                memorized_prefix = ""
            # Do not forget to report system message prefix, if any
        if memorized_prefix:
            super().emit(memorized_prefix)
