"""XML-based configuration load routines"""

from __future__ import annotations

import typing as t
from xml.etree import ElementTree

from .base import BaseConfigLoader

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
                self._parse_action_from_origin(child_node)
            elif child_node.tag == "Import":
                self._parse_import(child_node)
            elif child_node.tag == "Checklists":
                self._parse_checklists(child_node)
            else:
                self._throw(f"Unknown child tag: {child_node.tag}")
