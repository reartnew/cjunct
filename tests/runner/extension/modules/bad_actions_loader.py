"""Check extension possibilities"""

from cjunct.config.loaders.default.yaml import DefaultYAMLConfigLoader


class BadEchoAction:
    """No args"""

    async def run(self) -> str:
        """Just check return"""
        return "I am a string!"


class ConfigLoader(DefaultYAMLConfigLoader):
    """Able to build echoes"""

    ACTION_FACTORIES = {
        **DefaultYAMLConfigLoader.ACTION_FACTORIES,
        "echo": BadEchoAction,  # type: ignore
    }
