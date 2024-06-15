"""Types collection"""

import dataclasses
import typing as t

EventType = str
OutcomeStorageType = t.Dict[str, str]

__all__ = [
    "EventType",
    "OutcomeStorageType",
    "Stderr",
    "StringTemplate",
    "ObjectTemplate",
    "RenderedStringTemplate",
]


class Stderr(str):
    """Strings related to standard error stream"""


class StringTemplate(str):
    """String arguments to be templated later"""


@dataclasses.dataclass
class ObjectTemplate:
    """Complex object expression to be rendered later"""

    expression: str


class RenderedStringTemplate(StringTemplate):
    """Rendered string arguments"""
