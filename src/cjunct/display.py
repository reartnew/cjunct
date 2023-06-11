"""Runner output processors"""

import textwrap

from .actions import ActionBase, ActionNet

__all__ = [
    "BaseDisplay",
    "NetPrefixDisplay",
]


class BaseDisplay:
    """Base class for possible customizations"""

    def __init__(self, net: ActionNet) -> None:
        self._actions: ActionNet = net

    # pylint: disable=unused-argument
    def emit_action_message(self, source: ActionBase, message: str) -> None:
        """Process a message from some source"""
        self.display(message)

    def on_finish(self) -> None:
        """Runner finish handler"""

    def display(self, message: str) -> None:
        """Send text to the end user"""
        print(message)


class NetPrefixDisplay(BaseDisplay):
    """Prefix-based display for action nets"""

    def __init__(self, net: ActionNet) -> None:
        super().__init__(net)
        self._action_names_max_len = max(map(len, self._actions))
        self._last_displayed_name: str = ""

    def emit_action_message(self, source: ActionBase, message: str) -> None:
        # Construct prefix based on previous emitter action name
        justification_len: int = self._action_names_max_len + 2  # "2" here stands for square brackets
        formatted_name: str = (
            f"[{source.name}]".ljust(justification_len)
            if self._last_displayed_name != source.name
            else " " * justification_len
        )
        self._last_displayed_name = source.name
        super().emit_action_message(
            source=source,
            message=textwrap.indent(message.rstrip("\n"), f"{formatted_name} | "),
        )

    def _display_status_banner(self) -> None:
        """Show a text banner with the status info"""
        justification_len: int = self._action_names_max_len + 9  # "9" here stands for (e.g.) "SUCCESS: "
        self.display("=" * justification_len)
        for _, action in self._actions.iter_actions_by_tier():
            self.display(f"{action.status}: {action.name}")

    def on_finish(self) -> None:
        self._display_status_banner()
