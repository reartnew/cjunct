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
    """
    CJUNCT_LOG_LEVEL:
    CJUNCT_ENV_FILE:
    CJUNCT_CONTEXT_DIRECTORY:
    CJUNCT_ACTIONS_SOURCE_FILE:
    CJUNCT_WORKFLOW_FILE:
    CJUNCT_CONFIG_LOADER_SOURCE_FILE:
    CJUNCT_DISPLAY_SOURCE_FILE:
    CJUNCT_STRATEGY_NAME:
    CJUNCT_FORCE_COLOR:
    CJUNCT_SHELL_INJECT_YIELD_FUNCTION:
    CJUNCT_EXTERNAL_MODULES_PATHS:
    CJUNCT_ACTIONS_CLASS_DEFINITIONS_DIRECTORY:
    CJUNCT_STRICT_OUTCOMES_RENDERING:
    """

    CJUNCT_LOG_LEVEL: str = OptionalString("")
    CJUNCT_ENV_FILE: str = OptionalString("")
    CJUNCT_CONTEXT_DIRECTORY: str = OptionalString("")  # Will be dropped next major release.
    CJUNCT_ACTIONS_SOURCE_FILE: str = OptionalString("")  # Will be dropped next major release.
    CJUNCT_WORKFLOW_FILE: str = OptionalString("")  # Replaces CJUNCT_ACTIONS_SOURCE_FILE
    CJUNCT_CONFIG_LOADER_SOURCE_FILE: str = OptionalString("")
    CJUNCT_DISPLAY_SOURCE_FILE: str = OptionalString("")
    CJUNCT_STRATEGY_NAME: str = OptionalString("")
    CJUNCT_FORCE_COLOR: t.Optional[bool] = OptionalTernary(None)  # type: ignore
    CJUNCT_SHELL_INJECT_YIELD_FUNCTION: bool = OptionalBoolean(True)  # type: ignore
    CJUNCT_EXTERNAL_MODULES_PATHS: t.List[str] = OptionalList([])
    CJUNCT_ACTIONS_CLASS_DEFINITIONS_DIRECTORY: t.List[str] = OptionalList([])
    CJUNCT_STRICT_OUTCOMES_RENDERING: bool = OptionalBoolean(True)  # type: ignore
