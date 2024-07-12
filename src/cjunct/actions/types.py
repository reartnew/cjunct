"""Types collection"""

import dataclasses
import typing as t

EventType = str
OutcomeStorageType = t.Dict[str, str]

__all__ = [
    "EventType",
    "OutcomeStorageType",
    "Stderr",
    "ObjectTemplate",
    "qualify_string_as_potentially_renderable",
]


class Stderr(str):
    """Strings related to standard error stream"""


@dataclasses.dataclass
class ObjectTemplate:
    """Complex object expression to be rendered later"""

    expression: str


def qualify_string_as_potentially_renderable(data: str) -> bool:
    """Check that a string should be templated later"""
    return "@{" in data
