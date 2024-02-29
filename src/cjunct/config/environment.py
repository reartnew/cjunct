"""Separate environment-centric module"""

import typing as t

from named_env import (
    EnvironmentNamespace,
    OptionalString,
    OptionalTernary,
    OptionalBoolean,
    OptionalList,
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
    CJUNCT_FORCE_COLOR: t.Optional[bool] = OptionalTernary(None)  # type: ignore
    CJUNCT_SHELL_INJECT_YIELD_FUNCTION: bool = OptionalBoolean(True)  # type: ignore
    CJUNCT_EXTERNAL_MODULES_PATHS: t.List[str] = OptionalList([])
