"""YAML-based configuration load routines"""

from __future__ import annotations

import typing as t

import dacite
import yaml

from .inspect import get_class_annotations
from .root import DefaultRootConfigLoader
from ....actions.base import ActionBase, ActionDependency, ArgsBase

__all__ = [
    "DefaultYAMLConfigLoader",
]


class ExtraTag(yaml.YAMLObject):
    """Extended processing entity"""

    def __init__(self, data: t.Any) -> None:
        self.data = data

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)


DACITE_CONFIG = dacite.Config(strict=True)


class ImportTag(ExtraTag):
    """Imports processing entity"""

    yaml_tag: str = "!import"


class ChecklistsDirectoryTag(ExtraTag):
    """Checklists processing entity"""

    yaml_tag: str = "!checklists-directory"


class YAMLLoader(yaml.SafeLoader):
    """Extension loader"""


for extra_tag_class in (ImportTag, ChecklistsDirectoryTag):
    YAMLLoader.add_constructor(extra_tag_class.yaml_tag, extra_tag_class.from_yaml)


class DefaultYAMLConfigLoader(DefaultRootConfigLoader):
    """Loader for YAML source files"""

    def _parse_import(self, tag: ImportTag) -> None:
        path: str = tag.data
        if not isinstance(path, str):
            self._throw(f"Unrecognized '!import' contents type: {type(path)!r} (expected a string)")
        if not path:
            self._throw(f"Empty import: {path!r}")
        self._internal_load(path)

    def _parse_checklists(self, tag: ChecklistsDirectoryTag) -> None:
        path: str = tag.data
        if not isinstance(path, str):
            self._throw(f"Unrecognized '!checklists-directory' contents type: {type(path)!r} (expected a string)")
        if not path:
            self._throw(f"Empty checklists-directory directive: {path!r}")
        self._load_checklists_from_directory(path)

    def _internal_loads(self, data: t.Union[str, bytes]) -> None:
        if isinstance(data, bytes):
            data = data.decode()
        root_node: dict = yaml.load(data, YAMLLoader)  # nosec
        if not isinstance(root_node, dict):
            self._throw(f"Unknown config structure: {type(root_node)!r} (should be a dict)")
        root_keys: t.Set[str] = set(root_node)
        if not root_keys:
            self._throw("Empty root dictionary (expecting 'actions')")
        if unrecognized_keys := root_keys - {"actions"}:
            self._throw(f"Unrecognized root keys: {sorted(unrecognized_keys)} (expecting 'actions' only)")
        actions: t.List[t.Union[dict, ImportTag]] = root_node["actions"]
        if not isinstance(actions, list):
            self._throw(f"'actions' contents should be a list (get {type(actions)!r})")
        for child_node in actions:
            if isinstance(child_node, dict):
                action: ActionBase = self._build_action_from_dict(child_node)
                self._register_action(action)
            elif isinstance(child_node, ImportTag):
                self._parse_import(child_node)
            elif isinstance(child_node, ChecklistsDirectoryTag):
                self._parse_checklists(child_node)
            else:
                self._throw(f"Unrecognized node type: {type(child_node)!r}")

    # pylint: disable=inconsistent-return-statements
    def _build_dependency_from_node(self, dep_node: t.Union[str, dict]) -> t.Tuple[str, ActionDependency]:
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

    def _build_action_from_dict(self, node: dict) -> ActionBase:
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
        if action_type not in self.ACTION_FACTORIES:
            self._throw(f"Unknown dispatched type: {action_type}")
        action_class: t.Type[ActionBase] = self.ACTION_FACTORIES[action_type]
        # Description
        description: t.Optional[str] = node.pop("description", None)
        if description is not None and not isinstance(description, str):
            self._throw(f"Unrecognized 'description' content type: {type(description)!r} (expected optional string)")
        # Dependencies
        deps_node: t.List[t.Union[str, dict]] = node.pop("depends_on", [])
        if not isinstance(deps_node, list):
            self._throw(f"Unrecognized 'depends_on' content type: {type(deps_node)!r} (expected a list)")
        dependencies: t.Dict[str, ActionDependency] = dict(
            self._build_dependency_from_node(dep_node) for dep_node in deps_node
        )
        args_instance: ArgsBase = self._build_args_from_the_rest_of_the_node(
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

    def _build_args_from_the_rest_of_the_node(
        self,
        action_name: str,
        action_class: t.Type[ActionBase],
        node: dict,
    ) -> ArgsBase:
        for mro_class in action_class.__mro__:
            if args_class := get_class_annotations(mro_class).get("args"):
                break
        else:
            self._throw(f"Couldn't find args descriptor for class {action_class.__name__}")
        try:
            return t.cast(ArgsBase, dacite.from_dict(args_class, node, DACITE_CONFIG))
        except ValueError as e:
            self._throw(f"Action {action_name!r}: {e}")
        except dacite.UnexpectedDataError as e:
            self._throw(f"Unrecognized keys for action {action_name!r}: {sorted(e.keys)}")
        except dacite.WrongTypeError as e:
            self._throw(f"Unrecognized {e.field_path!r} content type: {type(e.value)} (expected {e.field_type!r})")
