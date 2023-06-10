"""
Runner has too many dependencies,
thus placed to a separate module.
"""

import asyncio
import functools
import typing as t
from pathlib import Path

import classlogging

from .actions import ActionNet, ActionBase
from .config.loaders import get_default_loader_class_for_file
from .config.loaders.base import BaseConfigLoader
from .display import NetPrefixDisplay, BaseDisplay
from .exceptions import SourceError
from .strategy import BaseStrategy, LooseStrategy

LoaderClassType = t.Type[BaseConfigLoader]
StrategyClassType = t.Type[BaseStrategy]
DisplayClassType = t.Type[BaseDisplay]

__all__ = [
    "Runner",
]


class Runner(classlogging.LoggerMixin):
    """Main entry object"""

    def __init__(
        self,
        config: t.Union[str, Path, None] = None,
        loader_class: t.Optional[LoaderClassType] = None,
        strategy_class: StrategyClassType = LooseStrategy,
        display_class: DisplayClassType = NetPrefixDisplay,
    ) -> None:
        self._config_path: Path = self._detect_config_source() if config is None else Path(config)
        self._loader_class: LoaderClassType = loader_class or get_default_loader_class_for_file(self._config_path)
        self.logger.debug(f"Using config loader class: {self._loader_class}")
        self._strategy_class: StrategyClassType = strategy_class
        self.logger.debug(f"Using strategy class: {self._strategy_class}")
        self._display_class: DisplayClassType = display_class
        self.logger.debug(f"Using display class: {self._display_class}")
        self._started: bool = False

    @functools.cached_property
    def actions(self) -> ActionNet:
        """Calculated actions net"""
        return self._loader_class().load(self._config_path)

    @functools.cached_property
    def display(self) -> BaseDisplay:
        """Attached display"""
        return self._display_class(net=self.actions)

    @classmethod
    def _detect_config_source(cls) -> Path:
        scan_path: Path = Path().resolve()
        cls.logger.debug(f"Looking for config files at {scan_path}")
        if (maybe_xml := scan_path / "network.xml").exists():
            cls.logger.info(f"Detected config source: {maybe_xml}")
            return maybe_xml
        raise SourceError(f"No config source detected in {scan_path}")

    async def run_async(self) -> None:
        """Primary coroutine for all further processing"""
        if self._started:
            raise RuntimeError("Runner has been started more than one time")
        self._started = True
        strategy: BaseStrategy = self._strategy_class(net=self.actions)
        action_tasks: t.List[asyncio.Task] = []
        async for action in strategy:  # type: ActionBase
            self.logger.trace(f"Allocating action iterator for {action.name!r}")
            for coro in (
                self._run_action(action=action),
                self._dispatch_action_events_to_display(action=action, display=self.display),
            ):
                action_tasks.append(asyncio.create_task(coro))

        for task in action_tasks:
            await task
        self.display.on_finish()

    @staticmethod
    async def _dispatch_action_events_to_display(action: ActionBase, display: BaseDisplay) -> None:
        async for message in action.read_events():
            display.emit_action_message(source=action, message=message)

    @staticmethod
    async def _run_action(action: ActionBase) -> None:
        await action

    def run_sync(self):
        """Wrap async run into an event loop"""
        asyncio.run(self.run_async())
