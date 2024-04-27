"""Base interface class for all loaders"""

from __future__ import annotations

import contextlib
import typing as t
from enum import Enum
from pathlib import Path

import dacite
from classlogging import LoggerMixin

from ..actions.base import ActionBase, ArgsBase, ActionDependency
from ..actions.types import StringTemplate
from ..exceptions import LoadError
from ..tools.inspect import get_class_annotations
from ..workflow import Workflow

__all__ = [
    "AbstractBaseWorkflowLoader",
]


class AbstractBaseWorkflowLoader(LoggerMixin):
    """Loaders base class"""

    STATIC_ACTION_FACTORIES: t.Dict[str, t.Type[ActionBase]] = {}

    def __init__(self) -> None:
        self._actions: t.Dict[str, ActionBase] = {}
        self._raw_file_names_stack: t.List[str] = []
        self._resolved_file_paths_stack: t.List[Path] = []
        self._gathered_context: t.Dict[str, t.Any] = {}

    def _register_action(self, action: ActionBase) -> None:
        if action.name in self._actions:
            self._throw(f"Action declared twice: {action.name!r}")
        self._actions[action.name] = action

    def _throw(self, message: str) -> t.NoReturn:
        """Raise loader exception from text"""
        raise LoadError(message=message, stack=self._raw_file_names_stack)

    def _internal_load(self, source_file: t.Union[str, Path]) -> None:
        """Load workflow partially from file (can be called recursively).
        :param source_file: either Path or string object pointing at a file"""
        with self._read_file(source_file) as file_data:
            self._internal_loads(file_data)

    def _get_context(self) -> Path:
        """Return active context directory for relative path resolution"""
        return self._resolved_file_paths_stack[-1].parent if self._resolved_file_paths_stack else Path()

    @contextlib.contextmanager
    def _read_file(self, source_file: t.Union[str, Path]) -> t.Iterator[bytes]:
        """Read file data"""
        source_file_raw_path: Path = Path(source_file)
        if not source_file_raw_path.is_absolute():
            source_file_raw_path = self._get_context() / source_file_raw_path
        source_resolved_file_path = source_file_raw_path.resolve()
        if source_resolved_file_path in self._resolved_file_paths_stack:
            self._throw("Cyclic load")
        self._raw_file_names_stack.append(str(source_file))
        self._resolved_file_paths_stack.append(source_resolved_file_path)
        self.logger.debug(f"Loading workflow file: {source_resolved_file_path}")
        try:
            if not source_resolved_file_path.is_file():
                self._throw(f"Workflow file not found: {source_resolved_file_path}")
            yield source_resolved_file_path.read_bytes()
        finally:
            self._raw_file_names_stack.pop()
            self._resolved_file_paths_stack.pop()

    def _internal_loads(self, data: t.Union[str, bytes]) -> None:
        """Load workflow partially from text (can be called recursively)"""
        raise NotImplementedError

    def _get_action_factory_by_type(self, action_type: str) -> t.Type[ActionBase]:
        if action_type not in self.STATIC_ACTION_FACTORIES:
            self._throw(f"Unknown dispatched type: {action_type}")
        return self.STATIC_ACTION_FACTORIES[action_type]

    def loads(self, data: t.Union[str, bytes]) -> Workflow:
        """Load workflow from text"""
        self._internal_loads(data=data)
        return Workflow(self._actions, context=self._gathered_context)

    def load(self, source_file: t.Union[str, Path]) -> Workflow:
        """Load workflow from file"""
        self._internal_load(source_file=source_file)
        return Workflow(self._actions, context=self._gathered_context)

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
        deps_node: t.Union[str, t.List[t.Union[str, dict]]] = node.pop("expects", [])
        if not isinstance(deps_node, str) and not isinstance(deps_node, list):
            self._throw(f"Unrecognized 'expects' content type: {type(deps_node)!r} (expected a string or list)")
        if isinstance(deps_node, str):
            deps_node = [deps_node]
        dependencies: t.Dict[str, ActionDependency] = dict(
            self.build_dependency_from_node(dep_node) for dep_node in deps_node
        )
        # Selectable
        selectable: bool = node.pop("selectable", True)
        if not isinstance(selectable, bool):
            self._throw(f"Unrecognized 'selectable' content type: {type(selectable)!r} (expected a bool)")
        # Make action instance
        args_instance: ArgsBase = self._build_args_from_the_rest_of_the_dict_node(
            action_name=name,
            action_class=action_class,
            node=node,
        )
        return action_class(
            name=name,
            args=args_instance,
            description=description,
            ancestors=dependencies,
            selectable=selectable,
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
                        cast=[Enum],
                        type_hooks={StringTemplate: self._ensure_string_template_hook},
                    ),
                ),
            )
        except ValueError as e:
            self._throw(f"Action {action_name!r}: {e}")
        except dacite.MissingValueError as e:
            self._throw(f"Missing key for action {action_name!r}: {e.field_path!r}")
        except dacite.UnexpectedDataError as e:
            self._throw(f"Unrecognized keys for action {action_name!r}: {sorted(e.keys)}")
        except dacite.WrongTypeError as e:
            self._throw(f"Unrecognized {e.field_path!r} content type: {type(e.value)} (expected {e.field_type!r})")
