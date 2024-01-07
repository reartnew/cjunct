"""Check extension possibilities"""

from dataclasses import dataclass

from cjunct.actions import ActionBase
from cjunct.config.loaders.default.yaml import DefaultYAMLConfigLoader


@dataclass
class EchoAction(ActionBase[None]):
    """Simple printer"""

    message: str = ""

    async def run(self) -> None:
        """Show message via display"""
        self.emit(self.message)


class StringReturningAction(ActionBase[str]):
    """Returns not none"""

    async def run(self) -> str:
        """Just check return"""
        return "I am a string!"


class ConfigLoader(DefaultYAMLConfigLoader):
    """Able to build echoes"""

    ACTION_FACTORIES = {
        **DefaultYAMLConfigLoader.ACTION_FACTORIES,
        "echo": EchoAction,
        "return-string": StringReturningAction,
    }

    def _build_action_from_dict(self, node: dict) -> ActionBase:
        action: ActionBase = super()._build_action_from_dict(node)
        # Varying args for echo
        if isinstance(action, EchoAction):
            action.message = self._parse_string_attr(attrib_name="message", node=node)
            if not action.message:
                self._throw(f"Action {action.name!r} message not specified")
        return action
