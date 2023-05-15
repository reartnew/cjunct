"""
DISCLAIMER:
As far as `fulcrum` is the project's close-sourced direct predecessor,
these loaders are used only temporarily to ensure local tests based on stable fulcrum-like configurations.
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field
from xml.etree import ElementTree

from .xml import XMLConfigLoader
from ...actions import ActionBase

__all__ = [
    "FulcrumXMLConfigLoader",
    "FulcrumAction",
]


@dataclass
class FulcrumAction(ActionBase):
    """Fulcrum-specific extension"""

    pushed_facts: t.Dict[str, t.Optional[str]] = field(default_factory=dict)
    skip_on_missing_inventory: bool = False
    needs_distribution: bool = False

    async def run(self) -> None:
        """A stub"""
        self.emit(f"{self.name}")


class FulcrumXMLConfigLoader(XMLConfigLoader):
    """Fulcrum-specific extension"""

    def _build_action_from_xml_node(self, node: ElementTree.Element) -> ActionBase:
        pushed_facts: t.Dict[str, t.Optional[str]] = {}
        skip_on_missing_inventory: bool = False
        needs_distribution: bool = False
        for sub_node in list(node):
            text = (sub_node.text or "").strip()
            if sub_node.tag == "script":
                sub_node.tag = "command"
            elif sub_node.tag == "pushFactToEnvironment":
                pushed_facts[text] = sub_node.attrib.get("label")
                node.remove(sub_node)
            elif sub_node.tag == "skipOnMissingInventory":
                skip_on_missing_inventory = text == "true"
                node.remove(sub_node)
            elif sub_node.tag == "needs-distribution":
                skip_on_missing_inventory = text == "true"
                node.remove(sub_node)
        action: FulcrumAction = t.cast(FulcrumAction, super()._build_action_from_xml_node(node=node))
        action.pushed_facts = pushed_facts
        action.skip_on_missing_inventory = skip_on_missing_inventory
        action.needs_distribution = needs_distribution
        return action

    ACTION_FACTORIES = {
        "groovy": FulcrumAction,
        "ansible": FulcrumAction,
    }
