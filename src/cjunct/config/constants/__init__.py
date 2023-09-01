"""Lazy-loaded constants"""

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
from ...strategy import LooseStrategy, KNOWN_STRATEGIES
from ...types import LoaderClassType
from ...types import StrategyClassType

__all__ = [
    "C",
]


def _get_strategy_from_cli_arg() -> t.Optional[StrategyClassType]:
    if (strategy_name := get_cli_arg("strategy")) is None:
        return None
    if strategy_name not in KNOWN_STRATEGIES:
        raise ValueError(f"Unrecognized strategy name: {strategy_name!r}. Expected one of: {sorted(KNOWN_STRATEGIES)}")
    return KNOWN_STRATEGIES[strategy_name]


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
        lambda: maybe_path(Env.CJUNCT_ACTIONS_SOURCE_FILE),
    )
    CONFIG_LOADER_SOURCE_FILE: Optional[LoaderClassType] = Optional(
        lambda: maybe_class_from_module(
            path_str=Env.CJUNCT_CONFIG_LOADER_SOURCE_FILE,
            class_name="ConfigLoader",
        )
    )
    STRATEGY_CLASS: Mandatory[StrategyClassType] = Mandatory(
        _get_strategy_from_cli_arg,
        lambda: Env.CJUNCT_STRATEGY_NAME or None,
        lambda: LooseStrategy,
    )
