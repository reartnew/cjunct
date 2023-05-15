"""
A strategy is an async-iterable object,
emitting actions one by one for further scheduling.
"""

import asyncio
import typing as t

import classlogging

from .actions import ActionNet, ActionBase

ST = t.TypeVar("ST", bound="BaseStrategy")

__all__ = [
    "BaseStrategy",
    "FreeStrategy",
    "SequentialStrategy",
    "LooseStrategy",
]


class BaseStrategy(classlogging.LoggerMixin, t.AsyncIterable[ActionBase]):
    """Strategy abstract base"""

    def __init__(self, net: ActionNet) -> None:
        self._actions = net

    def __aiter__(self: ST) -> ST:
        return self

    async def __anext__(self) -> ActionBase:
        raise NotImplementedError


class FreeStrategy(BaseStrategy):
    """Free execution (fully parallel)"""

    def __init__(self, net: ActionNet) -> None:
        super().__init__(net)
        self._unprocessed: t.List[ActionBase] = list(net.values())

    async def __anext__(self) -> ActionBase:
        if not self._unprocessed:
            raise StopAsyncIteration
        return self._unprocessed.pop(0)


class SequentialStrategy(FreeStrategy):
    """Sequential execution"""

    def __init__(self, net: ActionNet) -> None:
        super().__init__(net)
        self._current: t.Optional[ActionBase] = None

    async def __anext__(self) -> ActionBase:
        if self._current is not None:
            await self._current
        self._current = await super().__anext__()
        return self._current


class LooseStrategy(BaseStrategy):
    """Simply keep tracking dependencies, but neither dependency `strict` flag nor ancestor status"""

    def __init__(self, net: ActionNet) -> None:
        super().__init__(net)
        # Actions that have been emitted by the strategy and not finished yet
        self._active_actions_map: t.Dict[str, ActionBase] = {}
        # Just a structured mutable copy of the dependency map
        self._action_blockers: t.Dict[str, t.Set[str]] = {name: set(net[name].ancestors) for name in net}

    def _get_maybe_next_action(self) -> t.Optional[ActionBase]:
        """Completely non-optimal (always scan all actions), but readable yet"""
        done_action_names: t.Set[str] = {action.name for action in self._actions.values() if action.done()}
        # Copy into a list for further possible pop
        for maybe_next_action_name, maybe_next_action_blockers in list(self._action_blockers.items()):
            maybe_next_action_blockers -= done_action_names
            if not maybe_next_action_blockers:
                self.logger.debug(f"Action {maybe_next_action_name!r} is ready for scheduling")
                self._action_blockers.pop(maybe_next_action_name)
                next_action: ActionBase = self._actions[maybe_next_action_name]
                self._active_actions_map[next_action.name] = next_action
                return next_action
        return None

    async def __anext__(self) -> ActionBase:
        # Do we have anything pending already?
        if maybe_next_action := self._get_maybe_next_action():
            return maybe_next_action
        # Await for any actions finished. Can't directly apply asyncio.wait to Action objects
        # since python 3.11's implementation requires too many methods from an awaitable object.
        active_actions: t.List[ActionBase] = list(self._active_actions_map.values())
        await asyncio.wait(
            [action.get_future() for action in active_actions],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for action in active_actions:  # type: ActionBase
            if action.done():
                self.logger.debug(f"Action {action.name!r} execution finished, removing from active mapping")
                del self._active_actions_map[action.name]
        # Maybe now?
        if maybe_next_action := self._get_maybe_next_action():
            return maybe_next_action
        raise StopAsyncIteration
