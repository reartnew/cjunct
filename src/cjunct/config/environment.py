"""Separate environment-centric module"""

from named_env import (
    EnvironmentNamespace,
    OptionalString,
)

__all__ = [
    "Env",
]


class Env(EnvironmentNamespace):
    """Environment variables"""

    CJUNCT_LOG_LEVEL: str = OptionalString("")
    CJUNCT_CONTEXT_DIRECTORY: str = OptionalString("")
    CJUNCT_ACTIONS_SOURCE_FILE: str = OptionalString("")
    CJUNCT_CONFIG_LOADER_SOURCE_FILE: str = OptionalString("")
    CJUNCT_DISPLAY_SOURCE_FILE: str = OptionalString("")
    CJUNCT_STRATEGY_NAME: str = OptionalString("")
