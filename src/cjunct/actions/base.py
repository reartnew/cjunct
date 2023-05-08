"""Everything related to a default action interpretation"""

from __future__ import annotations

import asyncio
import inspect
import typing as t
from dataclasses import dataclass, field
from xml.etree import ElementTree

from async_shell import Shell
from classlogging import LoggerMixin

from ..exceptions import ActionStructureError

__all__ = [
    "Action",
    "ActionDependency",
]

AT = t.TypeVar("AT", bound="Action")


@dataclass
class ActionDependency:
    """Dependency info holder"""

    strict: bool = False
    external: bool = False


class ActionBase:
    """Base class for all actions"""

    _TYPE_HANDLERS: dict[str, t.Callable] = {}
    _HANDLER_MARK: str = "__cjunct_type_handler__"

    @classmethod
    def type_handler(cls, type_name: str):
        """Handler wrapper"""

        def wrapper(func):
            assert inspect.isasyncgenfunction(func)
            assert len(inspect.signature(func).parameters) == 1
            setattr(func, cls._HANDLER_MARK, getattr(func, cls._HANDLER_MARK, []) + [type_name])
            return func

        return wrapper

    def __init_subclass__(cls, **kwargs):
        default_handlers = []
        for maybe_handler in cls.__dict__.values():
            for handler_name in getattr(maybe_handler, cls._HANDLER_MARK, default_handlers):
                cls._TYPE_HANDLERS[handler_name] = maybe_handler


@dataclass
class Action(ActionBase, LoggerMixin):
    """Default action class.
    Supports only shell commands handling."""

    @ActionBase.type_handler("shell")
    async def _run_shell(self) -> t.AsyncGenerator[str, None]:
        async with Shell(self.command) as proc:
            async for line in proc.read_stdout():
                yield line
            await proc.validate()

    async def run(self) -> t.AsyncGenerator[str, None]:
        """Dispatch to the right generator handler"""
        unbound_callable = self._TYPE_HANDLERS[self.type]
        try:
            async for str_event in unbound_callable(self):
                yield str_event
        finally:
            self._finish_flag.set_result(None)

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
    # Do not create Future on constructing object to decouple from the event loop
    _maybe_finish_flag: t.Optional[asyncio.Future] = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        if self.type not in self._TYPE_HANDLERS:
            raise ActionStructureError(f"Unknown dispatched type: {self.type}")

    @property
    def _finish_flag(self) -> asyncio.Future:
        if self._maybe_finish_flag is None:
            self._maybe_finish_flag = asyncio.get_event_loop().create_future()
        return self._maybe_finish_flag

    def __await__(self) -> t.Generator:
        return self._finish_flag.__await__()

    def done(self) -> bool:
        """Indicate whether the action is over"""
        return self._finish_flag.done()

    # pylint: disable=inconsistent-return-statements
    @classmethod
    def build_from_origin(cls: t.Type[AT], origin: t.Any) -> AT:
        """Prepare an instance from raw contents.
        :raises:
            ActionStructureError: in a structure problem case"""
        if isinstance(origin, ElementTree.Element):
            return cls._build_from_xml(node=origin)
        raise ActionStructureError(f"Non-recognized origin: {origin}")

    @classmethod
    def _build_from_xml(cls: t.Type[AT], node: ElementTree.Element) -> AT:
        if (node.text or "").strip():
            raise ActionStructureError(f"Non-degenerate action node text: {node.text!r}")
        bad_attribs: t.Set[str] = set(node.attrib) - {"name", "onFail", "visible"}
        if bad_attribs:
            raise ActionStructureError(f"Unrecognized action node attributes: {sorted(bad_attribs)}")
        if "name" not in node.attrib:
            raise ActionStructureError("Missing action node required attribute: 'name'")
        name: str = node.attrib["name"]
        if not name:
            raise ActionStructureError("Action node name is empty")
        on_fail: t.Optional[str] = node.attrib.get("onFail")
        if on_fail not in (None, "warn", "stop"):
            raise ActionStructureError(
                f"Invalid 'onFail' attribute value {on_fail!r} (may be one of 'warn' and 'stop', or not set)"
            )
        visible_str: t.Optional[str] = node.attrib.get("visible")
        if visible_str not in (None, "true", "false"):
            raise ActionStructureError(
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
                raise ActionStructureError(f"Unrecognized tag: {xml_property.tag!r}")
            tag_value: str = (xml_property.text or "").strip()
            if xml_property.tag == "type":
                if action_type:
                    raise ActionStructureError(f"'type' is double-declared for action {name}")
                if xml_property.attrib:
                    raise ActionStructureError(f"'type' tag can't have given attributes: {sorted(xml_property.attrib)}")
                action_type = tag_value
            elif xml_property.tag == "dependency":
                if tag_value in dependencies:
                    raise ActionStructureError(f"Dependency {tag_value!r} is double-declared for action {name}")
                dependency: ActionDependency = ActionDependency()
                for attr_name, attr_value in xml_property.attrib.items():
                    if attr_name != "type":
                        raise ActionStructureError(f"'dependency' tag can't have given attribute: {attr_name!r}")
                    for dependency_type_marker in attr_value.split():
                        if dependency_type_marker == "strict":
                            dependency.strict = True
                        elif dependency_type_marker == "external":
                            dependency.external = True
                        else:
                            raise ActionStructureError(f"Unknown dependency type marker: {dependency_type_marker!r}")
                dependencies[tag_value] = dependency
            elif xml_property.tag == "description":
                if description is not None:
                    raise ActionStructureError(f"'description' is double-declared for action {name}")
                if xml_property.attrib:
                    raise ActionStructureError(
                        f"'description' tag can't have given attributes: {sorted(xml_property.attrib)}"
                    )
                description = tag_value
            elif xml_property.tag == "command":
                if action_command is not None:
                    raise ActionStructureError(f"Command is defined twice for action {name!r}")
                if not tag_value:
                    raise ActionStructureError(f"Command might not be empty for action {name!r}")
                if xml_property.attrib:
                    raise ActionStructureError(
                        f"'command' tag can't have given attributes: {sorted(xml_property.attrib)}"
                    )
                action_command = tag_value

        if action_command is None:
            raise ActionStructureError(f"Action {name!r} command is not specified")
        return cls(
            origin=node,
            name=name,
            type=action_type,
            command=action_command,
            on_fail=on_fail,
            visible=visible,
            description=description,
            ancestors=dependencies,
        )

    def __hash__(self) -> int:
        return hash(self.name)
