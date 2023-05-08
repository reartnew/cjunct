"""Check action parsing"""

from xml.etree import ElementTree

from cjunct.actions import Action


def test_ok():
    """Normal action sample"""
    root_node = ElementTree.XML(
        """
        <Action name="Foo">
            <description>Simple printer</description>
            <type>shell</type>
            <command>echo foo</command>
        </Action>
        """
    )
    Action.build_from_origin(root_node)
