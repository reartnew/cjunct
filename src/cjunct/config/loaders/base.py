from __future__ import annotations

import typing as t
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

from classlogging import LoggerMixin

__all__ = [
    "LoadError",
    "BaseConfigLoader",
    "Action",
]

AT = t.TypeVar("AT", bound="Action")


class LoadError(Exception):
    """Loader regular exception during load process"""

    def __init__(self, message: str, stack: t.List[str]) -> None:
        self.message: str = message
        self.stack: t.List[str] = stack
        text: str = message
        if stack:
            text += f"\nCurrent stack: {' -> '.join(stack)}"
        super().__init__(text)


class BaseConfigLoader(LoggerMixin):
    """Loaders base class"""

    def __init__(self) -> None:
        self._actions: t.Dict[str, Action] = {}
        self._files_stack: t.List[str] = []
        self._checklists: t.Dict[str, t.List[str]] = {}

    def throw(self, message: str) -> t.NoReturn:
        """Raise loader exception from text"""
        raise LoadError(message=message, stack=self._files_stack)

    def load_checklists_from_directory(self, directory: t.Union[str, Path]) -> None:
        """Parse checklists directory safely"""
        directory_path: Path = Path(directory)
        if not directory_path.is_dir():
            self.throw(f"No such directory: {directory_path}")
        for checklist_file in directory_path.iterdir():  # type: Path
            if not checklist_file.is_file():
                self.throw(f"Checklist is not a file: {checklist_file}")
            if checklist_file.suffix != ".checklist":
                self.throw(f"Checklist file has invalid extension: {checklist_file} (should be '.checklist')")
            checklist_name: str = checklist_file.stem
            if checklist_name in self._checklists:
                self.throw(f"Checklist defined twice: {checklist_name!r}")
            self._checklists[checklist_name] = [
                action_name.strip()
                for action_name in checklist_file.read_text(encoding="utf-8").splitlines()
                if action_name.strip()
            ]

    def load(self, source_file: t.Union[str, Path]) -> None:
        """Load from file.
        :param source_file: either Path or string object pointing at a file"""
        source_file_path: Path = Path(source_file)
        self._files_stack.append(str(source_file_path))
        self.logger.debug(f"Loading config file: {source_file_path}")
        try:
            if not source_file_path.is_file():
                self.throw(f"Config file not found: {source_file_path}")
            self.loads(source_file_path.read_bytes())
        finally:
            self._files_stack.pop()

    def loads(self, data: t.Union[str, bytes]) -> None:
        """Load from text. Should be implemented in subclasses."""
        raise NotImplementedError

    def get_tree(self) -> dict:
        """???"""
        return self._actions


@dataclass
class Action(LoggerMixin):
    """Default action class"""

    loader: BaseConfigLoader = field(repr=False)
    origin: t.Any = field(repr=False)
    name: str
    command: str
    on_fail: t.Optional[str] = None
    visible: bool = True
    dependencies: t.Dict[str, int] = field(default_factory=dict)
    description: t.Optional[str] = None

    # pylint: disable=inconsistent-return-statements
    @classmethod
    def build_from_origin(cls: t.Type[AT], origin: t.Any, loader: BaseConfigLoader) -> AT:
        """Prepare an instance from raw contents"""
        if isinstance(origin, ElementTree.Element):
            return cls._build_from_xml(node=origin, loader=loader)
        loader.throw(f"Non-recognized origin: {origin}")

    @classmethod
    def _build_from_xml(cls: t.Type[AT], node: t.Any, loader: BaseConfigLoader) -> AT:
        if node.text.strip():
            loader.throw(f"Non-degenerate action node text: {node.text!r}")
        bad_attribs: t.Set[str] = set(node.attrib) - {"name", "onFail", "visible"}
        if bad_attribs:
            loader.throw(f"Unrecognized action node attributes: {sorted(bad_attribs)}")
        if "name" not in node.attrib:
            loader.throw("Missing action node required attribute: 'name'")
        name: str = node.attrib["name"]
        if not name:
            loader.throw("Action node name is empty")
        on_fail: t.Optional[str] = node.attrib.get("onFail")
        if on_fail not in (None, "warn", "stop"):
            loader.throw(f"Invalid 'onFail' attribute value {on_fail!r} (may be one of 'warn' and 'stop', or not set)")
        visible_str: t.Optional[str] = node.attrib.get("visible")
        if visible_str not in (None, "true", "false"):
            loader.throw(
                f"Invalid 'visible' attribute value {visible_str!r} "
                f"(may be one of 'true' and 'false', or not set, which is considered visible)"
            )
        visible: bool = visible_str != "false"
        description: t.Optional[str] = None
        dependencies: t.Dict[str, int] = {}
        action_type: str = ""
        action_command: t.Optional[str] = None
        for xml_property in node:
            assert xml_property.tag in (
                "type",
                "description",
                "dependency",
                "command",
                # TODO: remove
                "script",
                "pushFactToEnvironment",
                "skipOnMissingInventory",
                "needs-distribution",
            ), xml_property.tag
            tag_value: str = xml_property.text.strip()
            if xml_property.tag == "type":
                if action_type:
                    loader.throw(f"'type' is double-declared for action {name}")
                if xml_property.attrib:
                    loader.throw(f"'type' tag can't have given attributes: {sorted(xml_property.attrib)}")
                action_type = tag_value
            elif xml_property.tag == "dependency":
                if tag_value in dependencies:
                    loader.throw(f"Dependency {tag_value!r} is double-declared for action {name}")
                dependency_type: int = 0
                for attr_name, attr_value in xml_property.attrib.items():
                    if attr_name != "type":
                        loader.throw(f"'dependency' tag can't have given attribute: {attr_name!r}")
                    for dependency_type_marker in attr_value.split():
                        if dependency_type_marker == "strict":
                            dependency_type |= 1
                        elif dependency_type_marker == "external":
                            dependency_type |= 2
                        else:
                            loader.throw(f"Unknown dependency type marker: {dependency_type_marker!r}")
                dependencies[tag_value] = dependency_type
            elif xml_property.tag == "description":
                if description is not None:
                    loader.throw(f"'description' is double-declared for action {name}")
                if xml_property.attrib:
                    loader.throw(f"'description' tag can't have given attributes: {sorted(xml_property.attrib)}")
                description = xml_property.text.strip()
            elif xml_property.tag in ("script", "command"):
                if action_command is not None:
                    loader.throw(f"Command is defined twice for action {name!r}")
                if not tag_value:
                    loader.throw(f"Command might not be empty for action {name!r}")
                if xml_property.attrib:
                    loader.throw(f"{xml_property.tag!r} tag can't have given attributes: {sorted(xml_property.attrib)}")
                action_command = tag_value

        if action_command is None:
            loader.throw(f"Action {name!r} command is not specified")
        return cls(
            loader=loader,
            origin=node,
            name=name,
            command=action_command,
            on_fail=on_fail,
            visible=visible,
            description=description,
            dependencies=dependencies,
        )
