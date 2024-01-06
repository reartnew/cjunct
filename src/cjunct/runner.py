"""
Runner has too many dependencies,
thus placed to a separate module.
"""

import asyncio
import functools
import typing as t
from pathlib import Path

import classlogging

from . import types
from .actions import ActionNet, ActionBase
from .config.constants import C
from .config.loaders import get_default_loader_class_for_file
from .display.base import BaseDisplay
from .display.default import NetPrefixDisplay
from .exceptions import SourceError, ExecutionFailed
from .strategy import BaseStrategy, LooseStrategy

__all__ = [
    "Runner",
]


class Runner(classlogging.LoggerMixin):
    """Main entry object"""

    def __init__(
        self,
        config: t.Union[str, Path, None] = None,
        loader_class: t.Optional[types.LoaderClassType] = None,
        strategy_class: types.StrategyClassType = LooseStrategy,
        display_class: types.DisplayClassType = NetPrefixDisplay,
    ) -> None:
        self._config_path: Path = self._detect_config_source() if config is None else Path(config)
        self._loader_class: types.LoaderClassType = (
            loader_class or C.CONFIG_LOADER_CLASS or get_default_loader_class_for_file(self._config_path)
        )
        self.logger.debug(f"Using config loader class: {self._loader_class}")
        self._strategy_class: types.StrategyClassType = strategy_class
        self.logger.debug(f"Using strategy class: {self._strategy_class}")
        self._display_class: types.DisplayClassType = display_class
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
        if C.ACTIONS_SOURCE_FILE is not None:
            source_file: Path = C.ACTIONS_SOURCE_FILE
            cls.logger.info(f"Using pre-configured actions source file: {source_file}")
            if not source_file.exists():
                raise SourceError(f"Pre-configured actions source file does not exist: {source_file}")
            return source_file
        scan_path: Path = C.CONTEXT_DIRECTORY
        cls.logger.debug(f"Looking for config files at {scan_path}")
        located_config_file: t.Optional[Path] = None
        for candidate_file_name in (
            "network.xml",
            "network.yml",
            "network.yaml",
        ):  # type: str
            if (maybe_config_file := scan_path / candidate_file_name).exists():
                cls.logger.info(f"Detected config source: {maybe_config_file}")
                if located_config_file is not None:
                    raise SourceError(f"Multiple config sources detected in {scan_path}")
                located_config_file = maybe_config_file
        if located_config_file is None:
            raise SourceError(f"No config source detected in {scan_path}")
        return located_config_file

    async def run_async(self) -> None:
        """Primary coroutine for all further processing"""
        if self._started:
            raise RuntimeError("Runner has been started more than one time")
        self._started = True
        strategy: BaseStrategy = self._strategy_class(net=self.actions)
        action_runners: t.Dict[str, asyncio.Task] = {}
        action_dispatchers: t.List[asyncio.Task] = []
        async for action in strategy:  # type: ActionBase
            self.logger.trace(f"Allocating action runner for {action.name!r}")
            action_runners[action.name] = asyncio.create_task(self._run_action(action=action))
            self.logger.trace(f"Allocating action dispatcher for {action.name!r}")
            action_dispatchers.append(
                asyncio.create_task(
                    self._dispatch_action_events_to_display(
                        action=action,
                        display=self.display,
                    )
                )
            )

        had_failed_tasks: bool = False
        for action_name, action_task in action_runners.items():
            try:
                action_result = await action_task
            except Exception as e:
                had_failed_tasks = True
                self.logger.info(f"Action {action_name!r} failed: {repr(e)}")
            else:
                if action_result is not None:
                    self.logger.warning(f"Action {action_name!r} returned something different from None")
        # Finalize dispatchers
        for dispatcher_task in action_dispatchers:
            await dispatcher_task

        self.display.on_finish()
        if had_failed_tasks:
            raise ExecutionFailed

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
