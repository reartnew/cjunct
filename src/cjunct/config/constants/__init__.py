"""Lazy-loaded constants"""

import typing as t
from pathlib import Path

import click
from classlogging import LogLevel

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
    "cliargs_receiver",
]

CLI_PARAMS: t.Dict[str, t.Any] = {}


def cliargs_receiver(func):
    """Store CLI args in the CLI_PARAMS container for further processing"""

    # pylint: disable=unused-argument
    def wrapped(ctx: click.Context, **kwargs):
        current_ctx: t.Optional[click.Context] = ctx
        while current_ctx:
            for k, v in current_ctx.params.items():
                if k not in CLI_PARAMS:
                    CLI_PARAMS[k] = v
            current_ctx = current_ctx.parent
        return func()

    return click.pass_context(wrapped)


class C:
    """Runtime constants"""

    LOG_LEVEL: Mandatory[str] = Mandatory(
        lambda: CLI_PARAMS.get("log_level"),
        lambda: Env.CJUNCT_LOG_LEVEL or None,
        lambda: LogLevel.ERROR,
    )
    CONTEXT_DIRECTORY: Mandatory[Path] = Mandatory(
        lambda: CLI_PARAMS.get("directory"),
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
