from __future__ import annotations

import typing as t
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

from classlogging import LoggerMixin

from .exceptions import LoadError
from ...commands import ShellCommand

__all__ = [
    "BaseConfigLoader",
    "Action",
]

AT = t.TypeVar("AT", bound="Action")


@dataclass
class ActionDependency:
    """Dependency info holder"""

    strict: bool = False
    external: bool = False


@dataclass
class Action(LoggerMixin):
    """Default action class"""

    loader: BaseConfigLoader = field(repr=False)
    origin: t.Any = field(repr=False)
    name: str
    type: str
    command: str
    on_fail: t.Optional[str] = field(default=None, repr=False)
    visible: bool = field(default=True, repr=False)
    ancestors: t.Dict[str, ActionDependency] = field(default_factory=dict, repr=False)
    description: t.Optional[str] = None
    descendants: t.Dict[str, ActionDependency] = field(init=False, default_factory=dict, repr=False)
    tier: t.Optional[int] = field(init=False, default=None, repr=False)

    # def __post_init__(self) -> None:
    #     if self.type != "shell":
    #         self.loader.throw(f"Unknown dispatched type: {self.type}")

    # pylint: disable=inconsistent-return-statements
    @classmethod
    def build_from_origin(cls: t.Type[AT], origin: t.Any, loader: BaseConfigLoader) -> AT:
        """Prepare an instance from raw contents"""
        if isinstance(origin, ElementTree.Element):
            return cls._build_from_xml(node=origin, loader=loader)
        loader.throw(f"Non-recognized origin: {origin}")

    @classmethod
    def _build_from_xml(cls: t.Type[AT], node: ElementTree.Element, loader: BaseConfigLoader) -> AT:
        if (node.text or "").strip():
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
        dependencies: t.Dict[str, ActionDependency] = {}
        action_type: str = ""
        action_command: t.Optional[str] = None
        for xml_property in node:
            if xml_property.tag not in (
                "type",
                "description",
                "dependency",
                "command",
            ):
                loader.throw(f"Unrecognized tag: {xml_property.tag!r}")
            tag_value: str = (xml_property.text or "").strip()
            if xml_property.tag == "type":
                if action_type:
                    loader.throw(f"'type' is double-declared for action {name}")
                if xml_property.attrib:
                    loader.throw(f"'type' tag can't have given attributes: {sorted(xml_property.attrib)}")
                action_type = tag_value
            elif xml_property.tag == "dependency":
                if tag_value in dependencies:
                    loader.throw(f"Dependency {tag_value!r} is double-declared for action {name}")
                dependency: ActionDependency = ActionDependency()
                for attr_name, attr_value in xml_property.attrib.items():
                    if attr_name != "type":
                        loader.throw(f"'dependency' tag can't have given attribute: {attr_name!r}")
                    for dependency_type_marker in attr_value.split():
                        if dependency_type_marker == "strict":
                            dependency.strict = True
                        elif dependency_type_marker == "external":
                            dependency.external = True
                        else:
                            loader.throw(f"Unknown dependency type marker: {dependency_type_marker!r}")
                dependencies[tag_value] = dependency
            elif xml_property.tag == "description":
                if description is not None:
                    loader.throw(f"'description' is double-declared for action {name}")
                if xml_property.attrib:
                    loader.throw(f"'description' tag can't have given attributes: {sorted(xml_property.attrib)}")
                description = tag_value
            elif xml_property.tag == "command":
                if action_command is not None:
                    loader.throw(f"Command is defined twice for action {name!r}")
                if not tag_value:
                    loader.throw(f"Command might not be empty for action {name!r}")
                if xml_property.attrib:
                    loader.throw(f"'command' tag can't have given attributes: {sorted(xml_property.attrib)}")
                action_command = tag_value

        if action_command is None:
            loader.throw(f"Action {name!r} command is not specified")
        return cls(
            loader=loader,
            origin=node,
            name=name,
            type=action_type,
            command=action_command,
            on_fail=on_fail,
            visible=visible,
            description=description,
            ancestors=dependencies,
        )


class BaseConfigLoader(LoggerMixin):
    """Loaders base class"""

    ACTION_FACTORY: t.Type[Action] = Action

    def __init__(self) -> None:
        self._actions: t.Dict[str, Action] = {}
        self._files_stack: t.List[str] = []
        self._checklists: t.Dict[str, t.List[str]] = {}
        self._loaded_file: t.Optional[Path] = None

    async def run(self) -> None:
        """Go-go power rangers"""
        for action in self._actions.values():
            command = ShellCommand(action=action)
            async for chunk in command.run():
                print(repr(chunk))
            print(command.succeeded)

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
        if self._loaded_file is None:
            # TODO: raise on double load
            self._loaded_file = source_file_path
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

    def _bootstrap(self) -> None:
        # Check dependencies integrity
        missing_non_external_deps: t.Set[str] = set()
        entrypoints: t.Set[str] = set()
        for action in self._actions.values():  # type: Action
            for dependency_action_name, dependency in list(action.ancestors.items()):
                if dependency_action_name not in self._actions:
                    if dependency.external:
                        # Get rid of missing external deps
                        action.ancestors.pop(dependency_action_name)
                    else:
                        missing_non_external_deps.add(dependency_action_name)
                    continue
                # Register symmetric descendant connection for further simplicity
                self._actions[dependency_action_name].descendants[action.name] = dependency
            # Check if there are any dependencies after removal at all
            if not action.ancestors:
                entrypoints.add(action.name)
        if missing_non_external_deps:
            self.throw(f"Missing actions among dependencies: {sorted(missing_non_external_deps)}")
        # Check entrypoints presence
        if not entrypoints:
            self.throw("No entrypoints for the graph")
        # Now go Dijkstra
        step_tier: int = 1
        tier_actions_names: t.Set[str] = entrypoints
        while True:
            next_tier_actions_names: t.Set[str] = set()
            for tier_action_name in tier_actions_names:
                tier_action: Action = self._actions[tier_action_name]
                if tier_action.tier is not None:
                    continue
                tier_action.tier = step_tier
                next_tier_actions_names |= set(tier_action.descendants)
            if not next_tier_actions_names:
                break
            step_tier += 1
            tier_actions_names = next_tier_actions_names
        self.logger.debug(f"Number of tiers for source file {self._loaded_file}: {step_tier}")
        unreachable_action_names: t.Set[str] = {action.name for action in self._actions.values() if action.tier is None}
        if unreachable_action_names:
            self.throw(f"Unreachable actions found: {sorted(unreachable_action_names)}")

    def get_tree_representation(self) -> str:
        """Return tree representation of the action graph"""
        self._bootstrap()
        return ""
