"""XML-based configuration load routines"""

from __future__ import annotations

import typing as t
from xml.etree import ElementTree

from .base import BaseConfigLoader
from ...actions.base import ActionBase, ActionDependency
from ...actions.shell import ShellAction

__all__ = [
    "XMLConfigLoader",
]


class XMLConfigLoader(BaseConfigLoader):
    """Loader extension for XML source files"""

    def _parse_import(self, node: ElementTree.Element) -> None:
        if node.attrib:
            self._throw(f"Unrecognized import attributes: {node.attrib!r}")
        if node.text is None:
            self._throw(f"Empty import: {node!r}")
        self._internal_load(node.text.strip())

    def _parse_checklists(self, node: ElementTree.Element) -> None:
        if node.text:
            self._throw(f"Unrecognized checklists node text: {node.text!r}")
        for attr_name, attr_value in node.attrib.items():
            if attr_name == "sourceDirectory":
                self._load_checklists_from_directory(attr_value)
            else:
                self._throw(f"Unrecognized checklists node attribute: {attr_name!r}")

    def _internal_loads(self, data: t.Union[str, bytes]) -> None:
        if isinstance(data, bytes):
            data = data.decode()
        root_node = ElementTree.XML(data)
        if root_node.tag != "Actions":
            self._throw(f"Unknown root tag: {root_node.tag!r} (should be 'Actions')")
        if root_node.attrib:
            self._throw(f"Unrecognized root attributes: {root_node.attrib!r}")
        for child_node in root_node:
            if child_node.tag == "Action":
                self._register_action(self._build_action_from_xml_node(child_node))
            elif child_node.tag == "Import":
                self._parse_import(child_node)
            elif child_node.tag == "Checklists":
                self._parse_checklists(child_node)
            else:
                self._throw(f"Unknown child tag: {child_node.tag}")

    def _build_action_from_xml_node(self, node: ElementTree.Element) -> ActionBase:
        if (node.text or "").strip():
            self._throw(f"Non-degenerate action node text: {node.text!r}")
        bad_attribs: t.Set[str] = set(node.attrib) - {"name", "onFail", "visible"}
        if bad_attribs:
            self._throw(f"Unrecognized action node attributes: {sorted(bad_attribs)}")
        if "name" not in node.attrib:
            self._throw("Missing action node required attribute: 'name'")
        name: str = node.attrib["name"]
        if not name:
            self._throw("Action node name is empty")
        on_fail: t.Optional[str] = node.attrib.get("onFail")
        if on_fail not in (None, "warn", "stop"):
            self._throw(f"Invalid 'onFail' attribute value {on_fail!r} (may be one of 'warn' and 'stop', or not set)")
        visible_str: t.Optional[str] = node.attrib.get("visible")
        if visible_str not in (None, "true", "false"):
            self._throw(
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
                self._throw(f"Unrecognized tag: {xml_property.tag!r}")
            tag_value: str = (xml_property.text or "").strip()
            if xml_property.tag == "type":
                if action_type:
                    self._throw(f"'type' is double-declared for action {name}")
                if xml_property.attrib:
                    self._throw(f"'type' tag can't have given attributes: {sorted(xml_property.attrib)}")
                action_type = tag_value
            elif xml_property.tag == "dependency":
                if tag_value in dependencies:
                    self._throw(f"Dependency {tag_value!r} is double-declared for action {name}")
                dependency: ActionDependency = ActionDependency()
                for attr_name, attr_value in xml_property.attrib.items():
                    if attr_name != "type":
                        self._throw(f"'dependency' tag can't have given attribute: {attr_name!r}")
                    for dependency_type_marker in attr_value.split():
                        if dependency_type_marker == "strict":
                            dependency.strict = True
                        elif dependency_type_marker == "external":
                            dependency.external = True
                        else:
                            self._throw(f"Unknown dependency type marker: {dependency_type_marker!r}")
                dependencies[tag_value] = dependency
            elif xml_property.tag == "description":
                if description is not None:
                    self._throw(f"'description' is double-declared for action {name}")
                if xml_property.attrib:
                    self._throw(f"'description' tag can't have given attributes: {sorted(xml_property.attrib)}")
                description = tag_value
            elif xml_property.tag == "command":
                if action_command is not None:
                    self._throw(f"Command is defined twice for action {name!r}")
                if not tag_value:
                    self._throw(f"Command might not be empty for action {name!r}")
                if xml_property.attrib:
                    self._throw(f"'command' tag can't have given attributes: {sorted(xml_property.attrib)}")
                action_command = tag_value

        if action_command is None:
            self._throw(f"Action {name!r} command is not specified")

        action_class: t.Type[ActionBase] = ShellAction
        return action_class(
            name=name,
            type=action_type,
            command=action_command,
            on_fail=on_fail,
            visible=visible,
            description=description,
            ancestors=dependencies,
        )
