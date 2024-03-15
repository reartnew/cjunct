"""YAML-based configuration load routines"""

from __future__ import annotations

import typing as t

import yaml

from .root import DefaultRootConfigLoader
from ....actions.base import ActionBase

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
        self.load_checklists_from_directory(path)

    def _internal_loads(self, data: t.Union[str, bytes]) -> None:
        if isinstance(data, bytes):
            data = data.decode()
        root_node: dict = yaml.load(data, YAMLLoader)  # nosec
        if not isinstance(root_node, dict):
            self._throw(f"Unknown config structure: {type(root_node)!r} (should be a dict)")
        root_keys: t.Set[str] = set(root_node)
        if not root_keys:
            self._throw("Empty root dictionary (expecting 'actions' or 'context')")
        if unrecognized_keys := root_keys - {"actions", "context"}:
            self._throw(f"Unrecognized root keys: {sorted(unrecognized_keys)} (expecting 'actions' or 'context')")
        if "actions" in root_node:
            actions: t.List[t.Union[dict, ImportTag]] = root_node["actions"]
            if not isinstance(actions, list):
                self._throw(f"'actions' contents should be a list (got {type(actions)!r})")
            for child_node in actions:
                if isinstance(child_node, dict):
                    action: ActionBase = self.build_action_from_dict_data(child_node)
                    self._register_action(action)
                elif isinstance(child_node, ImportTag):
                    self._parse_import(child_node)
                elif isinstance(child_node, ChecklistsDirectoryTag):
                    self._parse_checklists(child_node)
                else:
                    self._throw(f"Unrecognized node type: {type(child_node)!r}")
        if "context" in root_node:
            context: t.Dict[str, str] = root_node["context"]
            if not isinstance(context, dict):
                self._throw(f"'context' contents should be a dict (got {type(context)!r})")
            for context_key, context_value in context.items():
                if not isinstance(context_key, str):
                    self._throw(f"Context keys should be strings (got {type(context_key)!r} for {context_key!r})")
                if not isinstance(context_value, str):
                    self._throw(f"Context values should be strings (got {type(context_value)!r} for {context_value!r})")
                # if context_key in self._gathered_context:
                #     self.logger.info(f"Context key redefined: {context_key}")
                # else:
                self.logger.info(f"Context key added: {context_key}")
                self._gathered_context[context_key] = context_value
