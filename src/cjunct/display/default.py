"""Runner output processor default"""

import typing as t

from .base import BaseDisplay
from .color import Color
from ..actions.base import ActionBase, ActionStatus
from ..actions.net import ActionNet
from ..actions.types import Stderr

__all__ = [
    "NetPrefixDisplay",
]


class NetPrefixDisplay(BaseDisplay):
    """Prefix-based display for action nets"""

    _STATUS_TO_COLOR: t.Dict[ActionStatus, t.Callable[[str], str]] = {
        ActionStatus.SKIPPED: Color.gray,
        ActionStatus.PENDING: Color.gray,
        ActionStatus.FAILURE: Color.red,
        ActionStatus.RUNNING: lambda x: x,
        ActionStatus.SUCCESS: Color.green,
    }

    def __init__(self, net: ActionNet) -> None:
        super().__init__(net)
        self._action_names_max_len = max(map(len, self._actions))
        self._last_displayed_name: str = ""

    def _make_prefix(self, source_name: str, mark: str = " "):
        """Construct prefix based on previous emitter action name"""
        justification_len: int = self._action_names_max_len + 2  # "2" here stands for square brackets
        formatted_name: str = (
            f"[{source_name}]".ljust(justification_len)
            if self._last_displayed_name != source_name
            else " " * justification_len
        )
        self._last_displayed_name = source_name
        return Color.gray(f"{formatted_name} {mark}| ")

    def emit_action_message(self, source: ActionBase, message: str) -> None:
        is_stderr: bool = isinstance(message, Stderr)
        line_prefix: str = self._make_prefix(source_name=source.name, mark="*" if is_stderr else " ")
        for line in message.splitlines():
            super().emit_action_message(
                source=source,
                message=f"{line_prefix}{Color.yellow(line) if is_stderr else line}",
            )

    def emit_action_error(self, source: ActionBase, message: str) -> None:
        line_prefix: str = self._make_prefix(source_name=source.name, mark="!")
        for line in message.splitlines():
            super().emit_action_error(
                source=source,
                message=f"{line_prefix}{Color.red(line)}",
            )

    def _display_status_banner(self) -> None:
        """Show a text banner with the status info"""
        justification_len: int = self._action_names_max_len + 9  # "9" here stands for (e.g.) "SUCCESS: "
        self.display(Color.gray("=" * justification_len))
        for _, action in self._actions.iter_actions_by_tier():
            color_wrapper: t.Callable[[str], str] = self._STATUS_TO_COLOR[action.status]
            self.display(f"{color_wrapper(action.status.value)}: {action.name}")

    def on_finish(self) -> None:
        self._display_status_banner()
