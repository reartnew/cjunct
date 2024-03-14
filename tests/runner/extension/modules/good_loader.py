"""Check extension possibilities"""

from dataclasses import dataclass

from cjunct import ActionBase, ArgsBase
from cjunct.config.loaders.default.yaml import DefaultYAMLConfigLoader
from external_test_lib.constant import TEST_SUFFIX  # type: ignore  # pylint: disable=wrong-import-order


@dataclass
class EchoArgs(ArgsBase):
    """Args for EchoAction"""

    message: str


class EchoAction(ActionBase):
    """Simple printer"""

    args: EchoArgs

    async def run(self) -> None:
        """Show message via display"""
        self.emit(f"{self.args.message}-{TEST_SUFFIX}")


class StringReturningAction(ActionBase):
    """Returns not none"""

    async def run(self) -> str:  # type: ignore
        """Just return something that's not None"""
        return "I am a string!"


class ConfigLoader(DefaultYAMLConfigLoader):
    """Able to build echoes"""

    STATIC_ACTION_FACTORIES = {
        **DefaultYAMLConfigLoader.STATIC_ACTION_FACTORIES,
        "echo": EchoAction,
        "return-string": StringReturningAction,
    }
