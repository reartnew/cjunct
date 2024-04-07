"""Check extension possibilities"""

from cjunct import ArgsBase
from cjunct.loader.default import DefaultYAMLConfigLoader


class ReservedArgs(ArgsBase):
    """Use reserved name"""

    name: str


class BadEchoAction:
    """Reserved args"""

    args: ReservedArgs

    async def run(self) -> str:
        """Just check return"""
        return f"I am a string: {self.args.name}"


class ConfigLoader(DefaultYAMLConfigLoader):
    """Able to build echoes"""

    STATIC_ACTION_FACTORIES = {
        **DefaultYAMLConfigLoader.STATIC_ACTION_FACTORIES,
        "echo": BadEchoAction,  # type: ignore
    }
