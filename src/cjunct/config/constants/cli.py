"""CLI arguments"""

import functools
import typing as t

import click

__all__ = [
    "cliargs_receiver",
    "get_cli_arg",
]

_CLI_PARAMS: t.Dict[str, t.Any] = {}


def cliargs_receiver(func):
    """Store CLI args in the _CLI_PARAMS container for further processing"""

    @functools.wraps(func)
    # pylint: disable=unused-argument
    def wrapped(ctx: click.Context, **kwargs):
        current_ctx: t.Optional[click.Context] = ctx
        while current_ctx:
            for k, v in current_ctx.params.items():
                if k not in _CLI_PARAMS:
                    _CLI_PARAMS[k] = v
            current_ctx = current_ctx.parent
        return func()

    return click.pass_context(wrapped)


def get_cli_arg(name: str) -> t.Any:
    """Obtain previously registered CLI argument"""

    return _CLI_PARAMS.get(name)
