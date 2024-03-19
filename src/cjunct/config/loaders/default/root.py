"""Bind action runners"""

import typing as t
from functools import lru_cache
from pathlib import Path

from ..base import AbstractBaseConfigLoader
from ...constants import C
from ...constants.helpers import maybe_class_from_module
from ....actions.base import ActionBase
from ....actions.bundled import (
    EchoAction,
    ShellAction,
    DockerShellAction,
)

__all__ = [
    "DefaultRootConfigLoader",
]


# pylint: disable=abstract-method
class DefaultRootConfigLoader(AbstractBaseConfigLoader):
    """Bind default actions to abstract base"""

    STATIC_ACTION_FACTORIES = {
        name: klass
        for name, klass in (
            ("echo", EchoAction),
            ("shell", ShellAction),
            ("docker-shell", DockerShellAction),
        )
        if klass is not None
    }

    def _get_action_factory_by_type(self, action_type: str) -> t.Type[ActionBase]:
        if (dynamically_resolved_action_class := self._load_external_action_factories().get(action_type)) is not None:
            return dynamically_resolved_action_class
        return super()._get_action_factory_by_type(action_type)

    @lru_cache(maxsize=1)
    def _load_external_action_factories(self) -> t.Dict[str, t.Type[ActionBase]]:
        dynamic_bases_map: t.Dict[str, t.Type[ActionBase]] = {}
        for class_directory in C.ACTION_CLASSES_DIRECTORIES:  # type: str
            class_directory_path = Path(class_directory).resolve()
            self.logger.info(f"Loading external action classes from {class_directory_path}")
            for class_file in class_directory_path.iterdir():
                if not class_file.is_file() or not class_file.suffix == ".py":
                    continue
                action_type: str = class_file.stem
                self.logger.info(f"Trying external action class source: {class_file}")
                action_class: t.Type[ActionBase] = t.cast(
                    t.Type[ActionBase],
                    maybe_class_from_module(
                        path_str=str(class_file),
                        class_name="Action",
                        submodule_name=f"actions.{action_type}",
                    ),
                )
                if action_type in dynamic_bases_map:
                    self.logger.warning(f"Class {action_type!r} is already defined: overriding from {class_file}")
                dynamic_bases_map[action_type] = action_class
        return dynamic_bases_map
