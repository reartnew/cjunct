"""Base interface class for all loaders"""

from __future__ import annotations

import typing as t
from pathlib import Path

import dacite
from classlogging import LoggerMixin

from .inspect import get_class_annotations
from ...actions.base import ActionBase, ArgsBase, ActionDependency, StringTemplate
from ...actions.net import ActionNet
from ...exceptions import LoadError

__all__ = [
    "AbstractBaseConfigLoader",
]


class AbstractBaseConfigLoader(LoggerMixin):
    """Loaders base class"""

    _RESERVED_CHECKLISTS_NAMES: t.Set[str] = {"ALL", "NONE"}
    STATIC_ACTION_FACTORIES: t.Dict[str, t.Type[ActionBase]] = {}

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

    def load_checklists_from_directory(self, directory: t.Union[str, Path]) -> None:
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

    def _get_action_factory_by_type(self, action_type: str) -> t.Type[ActionBase]:
        if action_type not in self.STATIC_ACTION_FACTORIES:
            self._throw(f"Unknown dispatched type: {action_type}")
        return self.STATIC_ACTION_FACTORIES[action_type]

    def loads(self, data: t.Union[str, bytes]) -> ActionNet:
        """Load config from text"""
        self._internal_loads(data=data)
        return ActionNet(self._actions)

    def load(self, source_file: t.Union[str, Path]) -> ActionNet:
        """Load config from file"""
        self._internal_load(source_file=source_file)
        return ActionNet(self._actions)

    def build_dependency_from_node(self, dep_node: t.Union[str, dict]) -> t.Tuple[str, ActionDependency]:
        """Unified method to process transform dependency source data"""
        dep_holder: ActionDependency = ActionDependency()
        if isinstance(dep_node, str):
            return dep_node, dep_holder
        if isinstance(dep_node, dict):
            unexpected_dep_keys: t.Set[str] = set(dep_node) - {"name", "strict", "external"}
            if unexpected_dep_keys:
                self._throw(f"Unrecognized dependency node keys: {sorted(unexpected_dep_keys)}")
            # Dependency name
            if "name" not in dep_node:
                self._throw(f"Name not specified for the dependency: {sorted(dep_node.items())}")
            dep_name: str = dep_node["name"]
            if not isinstance(dep_name, str):
                self._throw(f"Unrecognized dependency name type: {type(dep_name)!r} (expected a string)")
            if not dep_name:
                self._throw("Empty dependency name met")
            # Dependency 'strict' attr
            strict: bool = dep_node.get("strict", False)
            if not isinstance(strict, bool):
                self._throw(f"Unrecognized 'strict' attribute type: {type(strict)!r} (expected boolean)")
            dep_holder.strict = strict
            # Dependency 'external' attr
            external: bool = dep_node.get("external", False)
            if not isinstance(external, bool):
                self._throw(f"Unrecognized 'external' attribute type: {type(external)!r} (expected boolean)")
            dep_holder.external = external
            return dep_name, dep_holder
        self._throw(f"Unrecognized dependency node structure: {type(dep_node)!r} (expected a string or a dict)")

    def build_action_from_dict_data(self, node: dict) -> ActionBase:
        """Process a dictionary representing an action"""
        # Action name
        if "name" not in node:
            self._throw("Missing action node required key: 'name'")
        name: str = node.pop("name")
        if not isinstance(name, str):
            self._throw(f"Unexpected name type: {type(name)!r} (should be a string")
        if not name:
            self._throw("Action node name is empty")
        # OnFail flag
        on_fail: t.Optional[str] = node.pop("on_fail", None)
        if on_fail not in (None, "warn", "stop"):
            self._throw(f"Invalid 'on_fail' value {on_fail!r} (may be one of 'warn' and 'stop', or not set)")
        # Visible flag
        visible_str: t.Optional[str] = node.pop("visible", None)
        if visible_str not in (None, "true", "false"):
            self._throw(
                f"Invalid 'visible' value {visible_str!r} "
                f"(may be one of 'true' and 'false', or not set, which is considered visible)"
            )
        visible: bool = visible_str != "false"
        # Action type
        if "type" not in node:
            self._throw(f"'type' not specified for action {name!r}")
        action_type: str = node.pop("type")
        action_class: t.Type[ActionBase] = self._get_action_factory_by_type(action_type)
        # Description
        description: t.Optional[str] = node.pop("description", None)
        if description is not None and not isinstance(description, str):
            self._throw(f"Unrecognized 'description' content type: {type(description)!r} (expected optional string)")
        # Dependencies
        deps_node: t.List[t.Union[str, dict]] = node.pop("expects", [])
        if not isinstance(deps_node, list):
            self._throw(f"Unrecognized 'expects' content type: {type(deps_node)!r} (expected a list)")
        dependencies: t.Dict[str, ActionDependency] = dict(
            self.build_dependency_from_node(dep_node) for dep_node in deps_node
        )
        args_instance: ArgsBase = self._build_args_from_the_rest_of_the_dict_node(
            action_name=name,
            action_class=action_class,
            node=node,
        )
        return action_class(
            name=name,
            args=args_instance,
            on_fail=on_fail,
            visible=visible,
            description=description,
            ancestors=dependencies,
        )

    @classmethod
    def _ensure_string_template_hook(cls, data: t.Any) -> StringTemplate:
        if not isinstance(data, str):
            raise dacite.WrongTypeError(
                field_type=StringTemplate,
                value=data,
            )
        return StringTemplate(data)

    def _build_args_from_the_rest_of_the_dict_node(
        self,
        action_name: str,
        action_class: t.Type[ActionBase],
        node: dict,
    ) -> ArgsBase:
        for mro_class in action_class.__mro__:
            if args_class := get_class_annotations(mro_class).get("args"):
                break
        else:
            self._throw(f"Couldn't find an `args` annotation for class {action_class.__name__}")
        try:
            return t.cast(
                ArgsBase,
                dacite.from_dict(
                    data_class=args_class,
                    data=node,
                    config=dacite.Config(
                        strict=True,
                        type_hooks={StringTemplate: self._ensure_string_template_hook},
                    ),
                ),
            )
        except ValueError as e:
            self._throw(f"Action {action_name!r}: {e}")
        except dacite.UnexpectedDataError as e:
            self._throw(f"Unrecognized keys for action {action_name!r}: {sorted(e.keys)}")
        except dacite.WrongTypeError as e:
            self._throw(f"Unrecognized {e.field_path!r} content type: {type(e.value)} (expected {e.field_type!r})")
