"""Check extension possibilities"""

from cjunct.loader.default import DefaultYAMLConfigLoader


class BadEchoAction:
    """No args"""

    async def run(self) -> str:
        """Just check return"""
        return "I am a string!"


class ConfigLoader(DefaultYAMLConfigLoader):
    """Able to build echoes"""

    STATIC_ACTION_FACTORIES = {
        **DefaultYAMLConfigLoader.STATIC_ACTION_FACTORIES,
        "echo": BadEchoAction,  # type: ignore
    }
