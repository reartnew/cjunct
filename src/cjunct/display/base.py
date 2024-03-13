"""Runner output processor base"""

from ..actions.base import ActionBase
from ..actions.net import ActionNet

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

    def on_finish(self) -> None:
        """Runner finish handler"""

    def display(self, message: str) -> None:
        """Send text to the end user"""
        print(message.rstrip("\n"))
