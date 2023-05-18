"""
DISCLAIMER:
As far as `fulcrum` is the project's close-sourced direct predecessor,
these loaders are used only temporarily to ensure local tests based on stable fulcrum-like configurations.
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from .xml import BaseXMLConfigLoader, XMLNode
from ...actions import ActionBase

__all__ = [
    "FulcrumXMLConfigLoader",
    "FulcrumAction",
]


@dataclass
class FulcrumAction(ActionBase):
    """Fulcrum-specific extension"""

    script: str = ""
    pushed_facts: t.Dict[str, t.Optional[str]] = field(default_factory=dict)
    skip_on_missing_inventory: bool = False
    needs_distribution: bool = False

    async def run(self) -> None:
        """A stub"""
        self.emit(self.name)


class FulcrumXMLConfigLoader(BaseXMLConfigLoader):
    """Fulcrum-specific extension"""

    def _build_action_from_xml_node(self, node: XMLNode) -> ActionBase:
        action: FulcrumAction = t.cast(FulcrumAction, super()._build_action_from_xml_node(node=node))
        for sub_node in node:
            if sub_node.tag == "script":
                action.script = sub_node.value
                sub_node.recognized = True
            elif sub_node.tag == "pushFactToEnvironment":
                action.pushed_facts[sub_node.value] = sub_node.attrib.get("label")
                sub_node.recognized = True
            elif sub_node.tag == "skipOnMissingInventory":
                action.skip_on_missing_inventory = sub_node.value == "true"
                sub_node.recognized = True
            elif sub_node.tag == "needs-distribution":
                action.skip_on_missing_inventory = sub_node.value == "true"
                sub_node.recognized = True
        return action

    ACTION_FACTORIES = {
        "groovy": FulcrumAction,
        "ansible": FulcrumAction,
    }
