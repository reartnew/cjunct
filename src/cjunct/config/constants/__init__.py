# pylint: disable=import-outside-toplevel,cyclic-import
"""Lazy-loaded constants"""

import os
import sys
import typing as t
from pathlib import Path

from classlogging import LogLevel

from .cli import get_cli_arg
from .helpers import (
    Optional,
    Mandatory,
    maybe_path,
    maybe_class_from_module,
)
from ..environment import Env
from ...types import (
    LoaderClassType,
    StrategyClassType,
    DisplayClassType,
)

__all__ = [
    "C",
]


def _maybe_strategy(name: t.Optional[str]) -> t.Optional[StrategyClassType]:
    """Transform an optional strategy name into an optional strategy class"""
    from ...strategy import KNOWN_STRATEGIES

    try:
        return KNOWN_STRATEGIES[name] if name else None
    except KeyError:
        raise ValueError(f"Invalid strategy name: {name!r} (allowed: {sorted(KNOWN_STRATEGIES)})") from None


def _get_default_display_class() -> DisplayClassType:
    from ...display.default import NetPrefixDisplay

    return NetPrefixDisplay


def _get_strategy_class_from_cli_arg() -> t.Optional[StrategyClassType]:
    from ...strategy import KNOWN_STRATEGIES

    return _maybe_strategy(get_cli_arg("strategy", valid_options=KNOWN_STRATEGIES))


def _get_default_strategy_class() -> StrategyClassType:
    from ...strategy import LooseStrategy

    return LooseStrategy


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
    ACTION_CLASSES_DIRECTORIES: Mandatory[t.List[str]] = Mandatory(
        lambda: Env.CJUNCT_ACTIONS_CLASS_DEFINITIONS_DIRECTORY,
    )
    DISPLAY_CLASS: Mandatory[DisplayClassType] = Mandatory(
        lambda: maybe_class_from_module(
            path_str=Env.CJUNCT_DISPLAY_SOURCE_FILE,
            class_name="Display",
        ),
        _get_default_display_class,
    )
    STRATEGY_CLASS: Mandatory[StrategyClassType] = Mandatory(
        _get_strategy_class_from_cli_arg,
        lambda: _maybe_strategy(Env.CJUNCT_STRATEGY_NAME),
        _get_default_strategy_class,
    )
    USE_COLOR: Mandatory[bool] = Mandatory(
        lambda: Env.CJUNCT_FORCE_COLOR,
        lambda: os.isatty(sys.stdout.fileno()),
    )
    SHELL_INJECT_YIELD_FUNCTION: Mandatory[bool] = Mandatory(
        lambda: Env.CJUNCT_SHELL_INJECT_YIELD_FUNCTION,
    )
