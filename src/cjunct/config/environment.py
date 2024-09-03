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
        Specifies the log level.
        Default is ERROR.
    CJUNCT_LOG_FILE:
        Specifies the log file.
        Defaults to the standard error stream.
    CJUNCT_ENV_FILE:
        Which file to load environment variables from. Expected format is k=v.
        Default is .env in the current directory.
    CJUNCT_WORKFLOW_FILE:
        Workflow file to use.
        Default behaviour is scan the current working directory.
    CJUNCT_WORKFLOW_LOADER_SOURCE_FILE:
        May point a file containing a WorkflowLoader class definition, which will replace the default implementation.
    CJUNCT_DISPLAY_NAME:
        Select the display by name from the bundled list.
    CJUNCT_DISPLAY_SOURCE_FILE:
        May point a file containing a Display class definition, which will replace the default implementation.
    CJUNCT_STRATEGY_NAME:
        Specifies the execution strategy.
        Default is 'loose'.
    CJUNCT_FORCE_COLOR:
        When specified, this will force the colored or non-coloured output, according to the setting.
    CJUNCT_SHELL_INJECT_YIELD_FUNCTION:
        When set to True, all shell-related actions will inject the yield_outcome function definition.
        Default is True.
    CJUNCT_EXTERNAL_MODULES_PATHS:
        A comma-separated list of local directories, which are added to the sys.path while loading any external modules.
        Default is an empty list.
    CJUNCT_ACTIONS_CLASS_DEFINITIONS_DIRECTORY:
        A comma-separated list of local directories, from which all `*.py` files will be considered action definitions.
        Each loaded definition is named after the filename stem and must contain an `Action` class.
        e.g. foo-bar.py may be referenced in a YAML workflow as `type: foo-bar`.
    CJUNCT_STRICT_OUTCOMES_RENDERING:
        When set to True, rendering a missing outcome key will result in an error instead of an empty string.
        Default is False.
    """

    CJUNCT_LOG_LEVEL: str = OptionalString("")
    CJUNCT_LOG_FILE: str = OptionalString("")
    CJUNCT_ENV_FILE: str = OptionalString("")
    CJUNCT_WORKFLOW_FILE: str = OptionalString("")
    CJUNCT_WORKFLOW_LOADER_SOURCE_FILE: str = OptionalString("")
    CJUNCT_DISPLAY_NAME: str = OptionalString("")
    CJUNCT_DISPLAY_SOURCE_FILE: str = OptionalString("")
    CJUNCT_STRATEGY_NAME: str = OptionalString("")
    CJUNCT_FORCE_COLOR: t.Optional[bool] = OptionalTernary(None)  # type: ignore
    CJUNCT_SHELL_INJECT_YIELD_FUNCTION: bool = OptionalBoolean(True)  # type: ignore
    CJUNCT_EXTERNAL_MODULES_PATHS: t.List[str] = OptionalList([])
    CJUNCT_ACTIONS_CLASS_DEFINITIONS_DIRECTORY: t.List[str] = OptionalList([])
    CJUNCT_STRICT_OUTCOMES_RENDERING: bool = OptionalBoolean(False)  # type: ignore
