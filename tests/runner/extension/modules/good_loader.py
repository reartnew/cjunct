"""Check extension possibilities"""

from cjunct import ActionBase
from cjunct.config.loaders.default.yaml import DefaultYAMLConfigLoader
from external_test_lib.constant import TEST_SUFFIX  # type: ignore  # pylint: disable=wrong-import-order


class StringReturningAction(ActionBase):
    """Returns not none"""

    async def run(self) -> str:  # type: ignore
        """Just return something that's not None"""
        return f"I am a string! {TEST_SUFFIX}"


class ConfigLoader(DefaultYAMLConfigLoader):
    """Able to build echoes"""

    STATIC_ACTION_FACTORIES = {
        **DefaultYAMLConfigLoader.STATIC_ACTION_FACTORIES,
        "return-string": StringReturningAction,
    }
