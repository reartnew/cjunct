"""Types collection"""

import typing as t

EventType = str
OutcomeStorageType = t.Dict[str, str]

__all__ = [
    "EventType",
    "OutcomeStorageType",
    "Stderr",
    "StringTemplate",
    "RenderedStringTemplate",
]


class Stderr(str):
    """Strings related to standard error stream"""


class StringTemplate(str):
    """String arguments to be templated later"""


class RenderedStringTemplate(StringTemplate):
    """Rendered string arguments"""
