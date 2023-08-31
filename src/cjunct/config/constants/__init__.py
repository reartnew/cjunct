"""Lazy-loaded constants"""

from pathlib import Path

from classlogging import LogLevel

from .cli import cli_arg_getter
from .helpers import (
    Optional,
    Mandatory,
    maybe_path,
    maybe_class_from_module,
)
from ..environment import Env
from ...types import LoaderClassType

__all__ = [
    "C",
]


class C:
    """Runtime constants"""

    LOG_LEVEL: Mandatory[str] = Mandatory(
        cli_arg_getter("log_level"),
        lambda: Env.CJUNCT_LOG_LEVEL or None,
        lambda: LogLevel.ERROR,
    )
    CONTEXT_DIRECTORY: Mandatory[Path] = Mandatory(
        cli_arg_getter("directory"),
        lambda: maybe_path(Env.CJUNCT_CONTEXT_DIRECTORY),
        lambda: Path().resolve(),
    )
    ACTIONS_SOURCE_FILE: Optional[Path] = Optional(
        lambda: maybe_path(Env.CJUNCT_ACTIONS_SOURCE_FILE),
    )
    CONFIG_LOADER_SOURCE_FILE: Optional[LoaderClassType] = Optional(
        lambda: maybe_class_from_module(
            path_str=Env.CJUNCT_CONFIG_LOADER_SOURCE_FILE,
            class_name="ConfigLoader",
        )
    )
