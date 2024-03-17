"""
Runner has too many dependencies,
thus placed to a separate module.
"""

import asyncio
import functools
import io
import sys
import typing as t
from dataclasses import asdict
from pathlib import Path

import classlogging
import dacite

from . import types
from .actions.base import ActionBase, ArgsBase
from .actions.net import ActionNet
from .actions.types import StringTemplate, RenderedStringTemplate
from .config.constants import C
from .config.loaders.base import AbstractBaseConfigLoader
from .config.loaders.helpers import get_default_loader_class_for_source
from .display.base import BaseDisplay
from .display.default import NetPrefixDisplay
from .exceptions import SourceError, ExecutionFailed, ActionRenderError, ActionRunError, ActionUnionRenderError
from .rendering import Templar
from .strategy import BaseStrategy, LooseStrategy

__all__ = [
    "Runner",
]

IOType = io.TextIOBase


class Runner(classlogging.LoggerMixin):
    """Main entry object"""

    def __init__(
        self,
        config: t.Union[str, Path, IOType, None] = None,
        loader_class: t.Optional[types.LoaderClassType] = None,
        strategy_class: types.StrategyClassType = LooseStrategy,
        display_class: types.DisplayClassType = NetPrefixDisplay,
    ) -> None:
        self._config_source: t.Union[Path, IOType] = (
            self._detect_config_source() if config is None else config if isinstance(config, IOType) else Path(config)
        )
        self._loader_class: types.LoaderClassType = (
            loader_class or C.CONFIG_LOADER_CLASS or get_default_loader_class_for_source(self._config_source)
        )
        self.logger.debug(f"Using config loader class: {self._loader_class}")
        self._strategy_class: types.StrategyClassType = strategy_class
        self.logger.debug(f"Using strategy class: {self._strategy_class}")
        self._display_class: types.DisplayClassType = display_class
        self.logger.debug(f"Using display class: {self._display_class}")
        self._started: bool = False
        self._outcomes: t.Dict[str, t.Dict[str, t.Any]] = {}
        self._had_failed_actions: bool = False

    @functools.cached_property
    def actions(self) -> ActionNet:
        """Calculated actions net"""
        loader: AbstractBaseConfigLoader = self._loader_class()
        return (
            loader.loads(self._config_source.read())
            if isinstance(self._config_source, io.TextIOBase)
            else loader.load(self._config_source)
        )

    @functools.cached_property
    def display(self) -> BaseDisplay:
        """Attached display"""
        return self._display_class(net=self.actions)

    @classmethod
    def _detect_config_source(cls) -> t.Union[Path, IOType]:
        if C.ACTIONS_SOURCE_FILE is not None:
            source_file: Path = C.ACTIONS_SOURCE_FILE
            if str(source_file) == "-":
                cls.logger.info("Using stdin as actions source")
                return t.cast(IOType, sys.stdin)
            if not source_file.exists():
                raise SourceError(f"Pre-configured actions source file does not exist: {source_file}")
            cls.logger.info(f"Using pre-configured actions source file: {source_file}")
            return source_file
        scan_path: Path = C.CONTEXT_DIRECTORY
        cls.logger.debug(f"Looking for config files at {scan_path}")
        located_config_file: t.Optional[Path] = None
        for candidate_file_name in (
            "cjunct.yml",
            "cjunct.yaml",
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
        background_tasks: t.List[asyncio.Task] = []
        async for action in strategy:  # type: ActionBase
            self.logger.trace(f"Allocating action runner for {action.name!r}")
            background_tasks.append(asyncio.create_task(self._run_action(action=action)))
            self.logger.trace(f"Allocating action dispatcher for {action.name!r}")
            background_tasks.append(
                asyncio.create_task(
                    self._dispatch_action_events_to_display(
                        action=action,
                        display=self.display,
                    )
                )
            )

        # Finalize running actions and message dispatchers
        for task in background_tasks:
            await task
        self.display.on_finish()
        if self._had_failed_actions:
            raise ExecutionFailed

    @staticmethod
    async def _dispatch_action_events_to_display(action: ActionBase, display: BaseDisplay) -> None:
        async for message in action.read_events():
            display.emit_action_message(source=action, message=message)

    async def _run_action(self, action: ActionBase) -> None:
        message: str
        try:
            self._render_action(action)
        except Exception as e:
            message = f"Action {action.name!r} rendering failed: {e}"
            self.display.emit_action_error(source=action, message=message)
            self.logger.warning(message, exc_info=not isinstance(e, ActionRenderError))
            action._internal_fail(e)  # pylint: disable=protected-access
            self._had_failed_actions = True
            return
        try:
            await action
        except Exception as e:
            self.display.emit_action_error(
                source=action,
                message=str(e) if isinstance(e, ActionRunError) else f"Action {action.name!r} run exception: {e!r}",
            )
            self.logger.warning(f"Action {action.name!r} execution failed: {e!r}")
            self.logger.debug("Action failure traceback", exc_info=True)
            self._had_failed_actions = True
        finally:
            self._outcomes[action.name] = action.get_outcomes()

    def run_sync(self):
        """Wrap async run into an event loop"""
        asyncio.run(self.run_async())

    def _render_action(self, action: ActionBase) -> None:
        """Prepare action to execution by rendering its template fields"""
        union_render_errors: t.List[str] = []

        def _string_template_render_hook(value: str) -> RenderedStringTemplate:
            templar: Templar = Templar(
                outcomes_getter=self._outcomes.get,
                status_getter=lambda name: self.actions[name].status.value if name in self.actions else None,
                raw_context_getter=self.actions.get_context_value,
            )
            try:
                return templar.render(value)
            except ActionRenderError as e:
                union_render_errors.append(str(e))
                raise

        original_args_dict: dict = asdict(action.args)
        try:
            rendered_args: ArgsBase = dacite.from_dict(
                data_class=type(action.args),
                data=original_args_dict,
                config=dacite.Config(
                    strict=True,
                    type_hooks={
                        StringTemplate: _string_template_render_hook,
                    },
                ),
            )
        # dacite union processing broadly suppresses all exceptions appearing during trying each type of the union
        except dacite.UnionMatchError as e:
            if not union_render_errors:
                # Native dacite error
                raise  # pragma: no cover
            raise ActionUnionRenderError("; ".join(union_render_errors)) from e
        action.args = rendered_args
