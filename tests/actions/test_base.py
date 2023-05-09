"""Check action parsing"""

from xml.etree import ElementTree

import pytest

from cjunct.actions import Action
from cjunct.exceptions import ActionStructureError


def test_xml_ok() -> None:
    """Normal action sample"""
    Action.build_from_origin(
        ElementTree.XML(
            """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
    <dependency type="strict external">Bar</dependency>
</Action>
            """
        )
    )


def test_xml_non_recognized_origin() -> None:
    """Unknown action source type"""
    with pytest.raises(ActionStructureError, match="Non-recognized origin"):
        Action.build_from_origin(None)


def test_xml_unknown_command_type() -> None:
    """Unexpected action command type"""
    with pytest.raises(ActionStructureError, match="Unknown dispatched type"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>UNEXPECTED</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_unexpected_node_text() -> None:
    """Unexpected text in the root node"""
    with pytest.raises(ActionStructureError, match="Non-degenerate action node text"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    UNEXPECTED TEXT
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_unexpected_attrs() -> None:
    """Unexpected attributes in the root node"""
    with pytest.raises(ActionStructureError, match="Unrecognized action node attributes"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo" unexpected="bar">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_missing_name() -> None:
    """Fail on name attribute absence"""
    with pytest.raises(ActionStructureError, match="Missing action node required attribute: 'name'"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action>
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_empty_name() -> None:
    """Fail on name attribute emptiness"""
    with pytest.raises(ActionStructureError, match="Action node name is empty"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_bad_on_fail_value() -> None:
    """Unexpected onFail attribute value"""
    with pytest.raises(ActionStructureError, match="Invalid 'onFail' attribute value"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo" onFail="bar">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_bad_visible_value() -> None:
    """Unexpected visible attribute value"""
    with pytest.raises(ActionStructureError, match="Invalid 'visible' attribute value"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo" visible="bar">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_bad_tag() -> None:
    """Unexpected tag"""
    with pytest.raises(ActionStructureError, match="Unrecognized tag"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
    <UNEXPECTED />
</Action>
                """
            )
        )


def test_xml_double_type() -> None:
    """Type declared twice"""
    with pytest.raises(ActionStructureError, match="'type' is double-declared for action"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_type_unexpected_attrs() -> None:
    """Type with attrs"""
    with pytest.raises(ActionStructureError, match="'type' tag can't have given attributes"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type bar="baz">shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_double_dependency() -> None:
    """Dependency declared twice"""
    with pytest.raises(ActionStructureError, match="Dependency .* is double-declared for action"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
    <dependency>Bar</dependency>
    <dependency>Bar</dependency>
</Action>
                """
            )
        )


def test_xml_dependency_unexpected_attrs() -> None:
    """Dependency unknown attrs"""
    with pytest.raises(ActionStructureError, match="'dependency' tag can't have given attribute"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
    <dependency bar="baz">Bar</dependency>
</Action>
                """
            )
        )


def test_xml_dependency_unknown_type() -> None:
    """Dependency unknown type"""
    with pytest.raises(ActionStructureError, match="Unknown dependency type marker"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
    <dependency type="baz">Bar</dependency>
</Action>
                """
            )
        )


def test_xml_double_description() -> None:
    """Description declared twice"""
    with pytest.raises(ActionStructureError, match="'description' is double-declared for action"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_description_unexpected_attrs() -> None:
    """Description unknown attrs"""
    with pytest.raises(ActionStructureError, match="'description' tag can't have given attributes"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description bar="baz">Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
    <dependency>Bar</dependency>
</Action>
                """
            )
        )


def test_xml_double_command() -> None:
    """Command declared twice"""
    with pytest.raises(ActionStructureError, match="Command is defined twice for action"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command>echo foo</command>
    <command>echo foo</command>
</Action>
                """
            )
        )


def test_xml_empty_command() -> None:
    """Command is empty"""
    with pytest.raises(ActionStructureError, match="Command might not be empty for action"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command />
</Action>
                """
            )
        )


def test_xml_command_unexpected_attrs() -> None:
    """Command unknown attrs"""
    with pytest.raises(ActionStructureError, match="'command' tag can't have given attributes"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
    <command bar="baz">echo foo</command>
    <dependency>Bar</dependency>
</Action>
                """
            )
        )


def test_xml_no_command() -> None:
    """Command undefined"""
    with pytest.raises(ActionStructureError, match="command is not specified"):
        Action.build_from_origin(
            ElementTree.XML(
                """
<Action name="Foo">
    <description>Simple printer</description>
    <type>shell</type>
</Action>
                """
            )
        )
