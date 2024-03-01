"""XML-based configuration load routines"""

from __future__ import annotations

import typing as t
from xml.etree.ElementTree import Element  # nosec

from defusedxml.ElementTree import XML  # type: ignore

from .root import DefaultRootConfigLoader
from ....actions.base import ActionBase, ActionDependency
from ....actions.shell import ShellAction

__all__ = [
    "BaseXMLConfigLoader",
    "DefaultXMLConfigLoader",
    "XMLNode",
]


class XMLNode:
    """Proxy object"""

    def __init__(self, element: Element) -> None:
        self._element = element
        self.recognized: bool = False
        self._children: t.Optional[t.List[XMLNode]] = None

    @property
    def value(self) -> str:
        """Truncated tag value"""
        return (self._element.text or "").strip()

    @staticmethod
    def loads(data: str) -> XMLNode:
        """Load from text"""
        return XMLNode(XML(data))

    def __iter__(self) -> t.Iterator[XMLNode]:
        if self._children is None:
            self._children = [XMLNode(element=sub_element) for sub_element in self._element]
        return iter(self._children)

    def __getattr__(self, item):
        return getattr(self._element, item)


class BaseXMLConfigLoader(DefaultRootConfigLoader):
    """Loader for XML source files"""

    def _parse_import(self, node: XMLNode) -> None:
        if node.attrib:
            self._throw(f"Unrecognized import attributes: {node.attrib!r}")
        if not node.value:
            self._throw(f"Empty import: {node!r}")
        self._internal_load(node.value)

    def _parse_checklists(self, node: XMLNode) -> None:
        if node.value:
            self._throw(f"Unrecognized checklists node text: {node.value!r}")
        for attr_name, attr_value in node.attrib.items():
            if attr_name == "sourceDirectory":
                self._load_checklists_from_directory(attr_value)
            else:
                self._throw(f"Unrecognized checklists node attribute: {attr_name!r}")

    def _internal_loads(self, data: t.Union[str, bytes]) -> None:
        if isinstance(data, bytes):
            data = data.decode()
        root_node = XMLNode.loads(data)
        if root_node.tag != "Actions":
            self._throw(f"Unknown root tag: {root_node.tag!r} (should be 'Actions')")
        if root_node.attrib:
            self._throw(f"Unrecognized root attributes: {root_node.attrib!r}")
        for child_node in root_node:
            if child_node.tag == "Action":
                action: ActionBase = self._build_action_from_xml_node(child_node)
                unrecognized_action_tags: t.List[str] = [tag.tag for tag in child_node if not tag.recognized]
                if unrecognized_action_tags:
                    self._throw(f"Unrecognized tags for action {action.name!r}: {unrecognized_action_tags}")
                self._register_action(action)
            elif child_node.tag == "Import":
                self._parse_import(child_node)
            elif child_node.tag == "Checklists":
                self._parse_checklists(child_node)
            else:
                self._throw(f"Unknown child tag: {child_node.tag}")

    def _build_action_from_xml_node(self, node: XMLNode) -> ActionBase:
        if node.value:
            self._throw(f"Non-degenerate action node text: {node.value!r}")
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
        for sub_node in node:  # type: XMLNode
            if sub_node.tag == "type":
                if action_type:
                    self._throw(f"'type' is double-declared for action {name}")
                if sub_node.attrib:
                    self._throw(f"'type' tag can't have given attributes: {sorted(sub_node.attrib)}")
                action_type = sub_node.value
                sub_node.recognized = True
            elif sub_node.tag == "dependency":
                if sub_node.value in dependencies:
                    self._throw(f"Dependency {sub_node.value!r} is double-declared for action {name}")
                dependency: ActionDependency = ActionDependency()
                for attr_name, attr_value in sub_node.attrib.items():
                    if attr_name != "type":
                        self._throw(f"'dependency' tag can't have given attribute: {attr_name!r}")
                    for dependency_type_marker in attr_value.split():
                        if dependency_type_marker == "strict":
                            dependency.strict = True
                        elif dependency_type_marker == "external":
                            dependency.external = True
                        else:
                            self._throw(f"Unknown dependency type marker: {dependency_type_marker!r}")
                dependencies[sub_node.value] = dependency
                sub_node.recognized = True
            elif sub_node.tag == "description":
                if description is not None:
                    self._throw(f"'description' is double-declared for action {name}")
                if sub_node.attrib:
                    self._throw(f"'description' tag can't have given attributes: {sorted(sub_node.attrib)}")
                description = sub_node.value
                sub_node.recognized = True

        if action_type not in self.ACTION_FACTORIES:
            self._throw(f"Unknown dispatched type: {action_type}")
        action_class: t.Type[ActionBase] = self.ACTION_FACTORIES[action_type]
        return action_class(
            name=name,
            # type=action_type,
            on_fail=on_fail,
            visible=visible,
            description=description,
            ancestors=dependencies,
        )


class DefaultXMLConfigLoader(BaseXMLConfigLoader):
    """Default extension for shell"""

    def _load_eponymous_tag(self, node: XMLNode, action: ActionBase) -> None:
        """Simple mandatory tag with no attrs"""
        action_attrib_name: str = node.tag
        if getattr(action, action_attrib_name):
            self._throw(f"{action_attrib_name.capitalize()} is defined twice for action {action.name!r}")
        if not node.value:
            self._throw(f"{action_attrib_name.capitalize()} might not be empty for action {action.name!r}")
        if node.attrib:
            self._throw(f"'{action_attrib_name}' tag can't have given attributes: {sorted(node.attrib)}")
        setattr(action, node.tag, node.value)
        node.recognized = True

    def _build_action_from_xml_node(self, node: XMLNode) -> ActionBase:
        action: ActionBase = super()._build_action_from_xml_node(node)
        # Varying args for shell
        if isinstance(action, ShellAction):
            for sub_node in node:
                if sub_node.tag in ("command", "script"):
                    self._load_eponymous_tag(node=sub_node, action=action)
            if not action.args.command and not action.args.script:
                self._throw(f"Action {action.name!r}: Neither command nor script specified")
            if action.args.command and action.args.script:
                self._throw(f"Action {action.name!r}: Both command and script specified")
        return action
