"""Runner output processor base"""

from ..actions.base import ActionBase
from ..actions.net import ActionNet
from ..exceptions import InteractionError

__all__ = [
    "BaseDisplay",
]


class BaseDisplay:
    """Base class for possible customizations"""

    def __init__(self, net: ActionNet) -> None:
        self._actions: ActionNet = net

    # pylint: disable=unused-argument
    def emit_action_message(self, source: ActionBase, message: str) -> None:
        """Process a message from some source"""
        self.display(message)

    # pylint: disable=unused-argument
    def emit_action_error(self, source: ActionBase, message: str) -> None:
        """Process an error from some source"""
        self.display(message)

    def on_finish(self) -> None:
        """Runner finish handler"""

    def on_plan_interaction(self, net: ActionNet) -> None:
        """Execution plan approval handler"""
        raise InteractionError

    def display(self, message: str) -> None:
        """Send text to the end user"""
        print(message.rstrip("\n"))
