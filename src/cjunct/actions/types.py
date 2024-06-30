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
]


class Stderr(str):
    """Strings related to standard error stream"""


StringTemplate = str


@dataclasses.dataclass
class ObjectTemplate:
    """Complex object expression to be rendered later"""

    expression: str
