"""CLI arguments"""

import typing as t
import click

__all__ = [
    "cliargs_receiver",
    "cli_arg_getter",
]

_CLI_PARAMS: t.Dict[str, t.Any] = {}


def cliargs_receiver(func):
    """Store CLI args in the _CLI_PARAMS container for further processing"""

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


def cli_arg_getter(name: str) -> t.Callable[[], t.Any]:
    """Obtain previously registered CLI argument"""

    def get():
        return _CLI_PARAMS.get(name)

    return get
