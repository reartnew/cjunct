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

    CJUNCT_CONTEXT_DIRECTORY = OptionalString("")
    CJUNCT_ACTIONS_SOURCE_FILE = OptionalString("")
