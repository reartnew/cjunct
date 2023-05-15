"""Base interface class for all loaders"""

from __future__ import annotations

import typing as t
from pathlib import Path

from classlogging import LoggerMixin

from ...actions import ActionNet, ActionBase
from ...actions.shell import ShellAction
from ...exceptions import LoadError

__all__ = [
    "BaseConfigLoader",
]


class BaseConfigLoader(LoggerMixin):
    """Loaders base class"""

    _RESERVED_CHECKLISTS_NAMES: t.Set[str] = {"ALL", "NONE"}
    ACTION_FACTORIES: t.Dict[str, t.Type[ActionBase]] = {"shell": ShellAction}

    def __init__(self) -> None:
        self._actions: t.Dict[str, ActionBase] = {}
        self._files_stack: t.List[str] = []
        self._checklists: t.Dict[str, t.List[str]] = {}
        self._loaded_file: t.Optional[Path] = None

    def _register_action(self, action: ActionBase) -> None:
        if action.name in self._actions:
            self._throw(f"Action declared twice: {action.name!r}")
        self._actions[action.name] = action

    def _throw(self, message: str) -> t.NoReturn:
        """Raise loader exception from text"""
        raise LoadError(message=message, stack=self._files_stack)

    def _load_checklists_from_directory(self, directory: t.Union[str, Path]) -> None:
        """Parse checklists directory safely"""
        directory_path: Path = Path(directory)
        if not directory_path.is_dir():
            self._throw(f"No such directory: {directory_path}")
        for checklist_file in directory_path.iterdir():  # type: Path
            if not checklist_file.is_file():
                self._throw(f"Checklist is not a file: {checklist_file}")
            if checklist_file.suffix != ".checklist":
                self._throw(f"Checklist file has invalid extension: {checklist_file} (should be '.checklist')")
            checklist_name: str = checklist_file.stem
            if checklist_name in self._checklists:
                self._throw(f"Checklist defined twice: {checklist_name!r}")
            if checklist_name in self._RESERVED_CHECKLISTS_NAMES:
                self._throw(f"Reserved checklist name used: {checklist_name!r}")
            self._checklists[checklist_name] = [
                action_name.strip()
                for action_name in checklist_file.read_text(encoding="utf-8").splitlines()
                if action_name.strip()
            ]

    def _internal_load(self, source_file: t.Union[str, Path]) -> None:
        """Load config partially from file (can be called recursively).
        :param source_file: either Path or string object pointing at a file"""
        source_file_path: Path = Path(source_file)
        if self._loaded_file is None:
            # TODO: raise on double load
            self._loaded_file = source_file_path
        self._files_stack.append(str(source_file_path))
        self.logger.debug(f"Loading config file: {source_file_path}")
        try:
            if not source_file_path.is_file():
                self._throw(f"Config file not found: {source_file_path}")
            self._internal_loads(source_file_path.read_bytes())
        finally:
            self._files_stack.pop()

    def _internal_loads(self, data: t.Union[str, bytes]) -> None:
        """Load config partially from text (can be called recursively)"""
        raise NotImplementedError

    def loads(self, data: t.Union[str, bytes]) -> ActionNet:
        """Load config from text"""
        self._internal_loads(data=data)
        return ActionNet(self._actions)

    def load(self, source_file: t.Union[str, Path]) -> ActionNet:
        """Load config from file"""
        self._internal_load(source_file=source_file)
        return ActionNet(self._actions)
