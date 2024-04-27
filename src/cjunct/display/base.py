"""Runner output processor base"""

from ..actions.base import ActionBase
from ..exceptions import InteractionError
from ..workflow import Workflow

__all__ = [
    "BaseDisplay",
]


class BaseDisplay:
    """Base class for possible customizations"""

    def __init__(self, workflow: Workflow) -> None:
        self._workflow: Workflow = workflow

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

    def on_plan_interaction(self, workflow: Workflow) -> None:
        """Execution plan approval handler"""
        raise InteractionError  # pragma: no cover

    def on_action_start(self, action: ActionBase) -> None:
        """Action start handler"""

    def on_action_finish(self, action: ActionBase) -> None:
        """Action finish handler"""

    def display(self, message: str) -> None:
        """Send text to the end user"""
        print(message.rstrip("\n"))
