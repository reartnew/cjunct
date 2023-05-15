"""Runner output processors"""

import textwrap
import typing as t

from .actions import ActionBase

__all__ = [
    "BaseDisplay",
    "NetPrefixDisplay",
]


class BaseDisplay:
    """Base class for possible customizations"""

    # pylint: disable=unused-argument
    def emit(self, source: ActionBase, message: str) -> None:
        """Process a message from some source"""
        print(message)


class NetPrefixDisplay(BaseDisplay):
    """Prefix-based display for action nets"""

    def __init__(self, net: t.Iterable[str]):
        super().__init__()
        self._justification_len = max(map(len, net)) + 2
        self._last_displayed_name: str = ""

    def emit(self, source: ActionBase, message: str) -> None:
        # Construct prefix based on previous emitter action name
        formatted_name: str = (
            f"[{source.name}]".ljust(self._justification_len)
            if self._last_displayed_name != source.name
            else " " * self._justification_len
        )
        self._last_displayed_name = source.name
        super().emit(
            source=source,
            message=textwrap.indent(message.rstrip("\n"), f"{formatted_name} | "),
        )
