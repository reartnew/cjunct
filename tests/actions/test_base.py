"""Check action parsing"""

import typing as t
from xml.etree import ElementTree

from cjunct.actions import Action


def _on_error(message: str) -> t.NoReturn:
    raise ValueError(message)


def test_ok():
    """Normal action sample"""
    root_node = ElementTree.XML(
        """
        <Action name="Single">
            <description>Run ansible</description>
            <type>shell</type>
            <command>playbooks/Dummy.yml</command>
        </Action>
        """
    )
    Action.build_from_origin(root_node, on_error=_on_error)
