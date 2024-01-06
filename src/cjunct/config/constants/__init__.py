"""Lazy-loaded constants"""

import os
import sys
from pathlib import Path

from classlogging import LogLevel

from .cli import get_cli_arg
from .helpers import (
    Optional,
    Mandatory,
    maybe_path,
    maybe_class_from_module,
    maybe_strategy,
)
from ..environment import Env
from ...strategy import LooseStrategy, KNOWN_STRATEGIES
from ...display import NetPrefixDisplay
from ...types import (
    LoaderClassType,
    StrategyClassType,
    DisplayClassType,
)

__all__ = [
    "C",
]


class C:
    """Runtime constants"""

    LOG_LEVEL: Mandatory[str] = Mandatory(
        lambda: get_cli_arg("log_level"),
        lambda: Env.CJUNCT_LOG_LEVEL or None,
        lambda: LogLevel.ERROR,
    )
    CONTEXT_DIRECTORY: Mandatory[Path] = Mandatory(
        lambda: get_cli_arg("directory"),
        lambda: maybe_path(Env.CJUNCT_CONTEXT_DIRECTORY),
        lambda: Path().resolve(),
    )
    ACTIONS_SOURCE_FILE: Optional[Path] = Optional(
        lambda: maybe_path(get_cli_arg("file")),
        lambda: maybe_path(Env.CJUNCT_ACTIONS_SOURCE_FILE),
    )
    CONFIG_LOADER_CLASS: Optional[LoaderClassType] = Optional(
        lambda: maybe_class_from_module(
            path_str=Env.CJUNCT_CONFIG_LOADER_SOURCE_FILE,
            class_name="ConfigLoader",
        )
    )
    DISPLAY_CLASS: Mandatory[DisplayClassType] = Mandatory(
        lambda: maybe_class_from_module(
            path_str=Env.CJUNCT_DISPLAY_SOURCE_FILE,
            class_name="Display",
        ),
        lambda: NetPrefixDisplay,
    )
    STRATEGY_CLASS: Mandatory[StrategyClassType] = Mandatory(
        lambda: maybe_strategy(get_cli_arg("strategy", valid_options=KNOWN_STRATEGIES)),
        lambda: maybe_strategy(Env.CJUNCT_STRATEGY_NAME),
        lambda: LooseStrategy,
    )
