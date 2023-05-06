"""Runner output processors"""

import textwrap
import typing as t

__all__ = [
    "BaseDisplay",
    "NetPrefixDisplay",
]


class BaseDisplay:
    """Base class for possible customizations"""

    # pylint: disable=unused-argument
    def emit(self, source: t.Any, message: str) -> None:
        """Process a message from some source"""
        print(message)


class NetPrefixDisplay(BaseDisplay):
    """Prefix-based display for action nets"""

    def __init__(self, net: t.Iterable[str]):
        super().__init__()
        self._justification_len = max(map(len, net)) + 2
        self._last_displayed_name: str = ""

    def emit(self, source: str, message: str) -> None:
        formatted_name: str = (
            f"[{source}]".ljust(self._justification_len)
            if self._last_displayed_name != source
            else " " * self._justification_len
        )
        self._last_displayed_name = source
        super().emit(
            source=source,
            message=textwrap.indent(message.rstrip("\n"), f"{formatted_name} | "),
        )
