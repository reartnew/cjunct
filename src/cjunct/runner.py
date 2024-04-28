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
from enum import Enum
from pathlib import Path

import classlogging
import dacite

from . import types
from .actions.base import ActionBase, ArgsBase
from .actions.types import StringTemplate, RenderedStringTemplate
from .config.constants import C
from .display.base import BaseDisplay
from .display.default import DefaultDisplay
from .exceptions import SourceError, ExecutionFailed, ActionRenderError, ActionRunError, ActionUnionRenderError
from .loader.base import AbstractBaseWorkflowLoader
from .loader.helpers import get_default_loader_class_for_source
from .rendering import Templar
from .strategy import BaseStrategy, LooseStrategy
from .workflow import Workflow

__all__ = [
    "Runner",
]

IOType = io.TextIOBase


class Runner(classlogging.LoggerMixin):
    """Main entry object"""

    def __init__(
        self,
        source: t.Union[str, Path, IOType, None] = None,
        loader_class: t.Optional[types.LoaderClassType] = None,
        strategy_class: types.StrategyClassType = LooseStrategy,
        display_class: types.DisplayClassType = DefaultDisplay,
    ) -> None:
        self._workflow_source: t.Union[Path, IOType] = (
            self._detect_workflow_source() if source is None else source if isinstance(source, IOType) else Path(source)
        )
        self._loader_class: types.LoaderClassType = (
            loader_class or C.WORKFLOW_LOADER_CLASS or get_default_loader_class_for_source(self._workflow_source)
        )
        self.logger.debug(f"Using workflow loader class: {self._loader_class}")
        self._strategy_class: types.StrategyClassType = strategy_class
        self.logger.debug(f"Using strategy class: {self._strategy_class}")
        self._display_class: types.DisplayClassType = display_class
        self.logger.debug(f"Using display class: {self._display_class}")
        self._started: bool = False
        self._outcomes: t.Dict[str, t.Dict[str, t.Any]] = {}
        self._had_failed_actions: bool = False

    @functools.cached_property
    def workflow(self) -> Workflow:
        """Calculated workflow"""
        loader: AbstractBaseWorkflowLoader = self._loader_class()
        return (
            loader.loads(self._workflow_source.read())
            if isinstance(self._workflow_source, io.TextIOBase)
            else loader.load(self._workflow_source)
        )

    @functools.cached_property
    def display(self) -> BaseDisplay:
        """Attached display"""
        return self._display_class(workflow=self.workflow)

    @classmethod
    def _detect_workflow_source(cls) -> t.Union[Path, IOType]:
        if C.ACTIONS_SOURCE_FILE is not None:
            source_file: Path = C.ACTIONS_SOURCE_FILE
            if str(source_file) == "-":
                cls.logger.info("Using stdin as workflow source")
                return t.cast(IOType, sys.stdin)
            if not source_file.exists():
                raise SourceError(f"Given workflow file does not exist: {source_file}")
            cls.logger.info(f"Using given workflow file: {source_file}")
            return source_file
        scan_path: Path = C.CONTEXT_DIRECTORY
        cls.logger.debug(f"Looking for workflow files at {str(scan_path)!r}")
        located_source_file: t.Optional[Path] = None
        for candidate_file_name in (
            "cjunct.yml",
            "cjunct.yaml",
        ):  # type: str
            if (maybe_source_file := scan_path / candidate_file_name).exists():
                cls.logger.info(f"Detected the workflow source: {str(maybe_source_file)!r}")
                if located_source_file is not None:
                    raise SourceError(f"Multiple workflow sources detected in {scan_path}")
                located_source_file = maybe_source_file
        if located_source_file is None:
            raise SourceError(f"No workflow source detected in {scan_path}")
        return located_source_file

    async def run_async(self) -> None:
        """Primary coroutine for all further processing"""
        if self._started:
            raise RuntimeError("Runner has been started more than one time")
        self._started = True
        strategy: BaseStrategy = self._strategy_class(workflow=self.workflow)
        if C.INTERACTIVE_MODE:
            self.display.on_plan_interaction(workflow=self.workflow)
        action_runners: t.Dict[ActionBase, asyncio.Task] = {}
        # Prefill outcomes map
        for action_name in self.workflow:
            self._outcomes[action_name] = {}
        async for action in strategy:  # type: ActionBase
            if not action.enabled:
                self.logger.debug(f"Skipping {action} as it is not enabled")
                continue
            # Finalize all actions that have been done already
            for maybe_finished_action, corresponding_runner_task in list(action_runners.items()):
                if maybe_finished_action.done():
                    self.logger.trace(f"Finalizing done action {maybe_finished_action.name!r} runner")
                    await corresponding_runner_task
                    action_runners.pop(maybe_finished_action)
            self.logger.trace(f"Allocating action runner for {action.name!r}")
            action_runners[action] = asyncio.create_task(self._run_action(action=action))

        # Finalize running actions
        for task in action_runners.values():
            await task
        try:
            self.display.on_finish()
        except Exception:
            self.logger.exception("`on_finish` failed")
        if self._had_failed_actions:
            raise ExecutionFailed

    @classmethod
    async def _dispatch_action_events_to_display(cls, action: ActionBase, display: BaseDisplay) -> None:
        try:
            async for message in action.read_events():
                display.emit_action_message(source=action, message=message)
        except Exception:
            cls.logger.exception(f"`emit_action_message` failed for {action.name!r}")

    async def _run_action(self, action: ActionBase) -> None:
        message: str
        try:
            self._render_action(action)
        except Exception as e:
            details: str = str(e) if isinstance(e, ActionRenderError) else repr(e)
            message = f"Action {action.name!r} rendering failed: {details}"
            self.display.emit_action_error(source=action, message=message)
            self.logger.warning(message, exc_info=not isinstance(e, ActionRenderError))
            action._internal_fail(e)  # pylint: disable=protected-access
            self._had_failed_actions = True
            return
        self.logger.trace(f"Calling `on_action_start` for {action.name!r}")
        try:
            self.display.on_action_start(action)
        except Exception:
            self.logger.exception(f"`on_action_start` failed for {action.name!r}")
        self.logger.trace(f"Allocating action dispatcher for {action.name!r}")
        action_events_reader_task: asyncio.Task = asyncio.create_task(
            self._dispatch_action_events_to_display(
                action=action,
                display=self.display,
            )
        )
        try:
            await action
        except Exception as e:
            try:
                self.display.emit_action_error(
                    source=action,
                    message=str(e) if isinstance(e, ActionRunError) else f"Action {action.name!r} run exception: {e!r}",
                )
            except Exception:
                self.logger.exception(f"`emit_action_error` failed for {action.name!r}")
            self.logger.warning(f"Action {action.name!r} execution failed: {e!r}")
            self.logger.debug("Action failure traceback", exc_info=True)
            self._had_failed_actions = True
        finally:
            self._outcomes[action.name].update(action.get_outcomes())
            await action_events_reader_task
            self.logger.trace(f"Calling `on_action_finish` for {action.name!r}")
            try:
                self.display.on_action_finish(action)
            except Exception:
                self.logger.exception(f"`on_action_finish` failed for {action.name!r}")

    def run_sync(self):
        """Wrap async run into an event loop"""
        asyncio.run(self.run_async())

    def _render_action(self, action: ActionBase) -> None:
        """Prepare action to execution by rendering its template fields"""
        union_render_errors: t.List[str] = []
        templar: Templar = Templar(
            outcomes_map=self._outcomes,
            action_states={name: self.workflow[name].status.value for name in self.workflow},
            context_map=self.workflow.context,
        )

        def _string_template_render_hook(value: str) -> RenderedStringTemplate:
            try:
                return templar.render(value)
            except ActionRenderError as are:
                union_render_errors.append(str(are))
                raise

        original_args_dict: dict = asdict(action.args)
        try:
            rendered_args: ArgsBase = dacite.from_dict(
                data_class=type(action.args),
                data=original_args_dict,
                config=dacite.Config(
                    strict=True,
                    cast=[Enum],
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
