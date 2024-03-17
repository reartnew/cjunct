"""Actions-related constants"""

import typing as t

__all__ = [
    "ACTION_RESERVED_FIELD_NAMES",
]

ACTION_RESERVED_FIELD_NAMES: t.Set[str] = {
    "name",
    "type",
    "description",
    "expects",
    "severity",  # planned in future
    "selectable",  # planned in future
}
