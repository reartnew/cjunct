"""CLI arguments"""

import functools
import typing as t

import click

__all__ = [
    "cliargs_receiver",
    "get_cli_arg",
]

_CLI_PARAMS: t.Dict[str, t.Any] = {}


def cliargs_receiver(func):  # pragma: no cover
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


def get_cli_arg(name: str, *, valid_options: t.Optional[t.Iterable[str]] = None) -> t.Any:
    """Obtain previously registered CLI argument"""

    value: t.Any = _CLI_PARAMS.get(name)
    if valid_options is not None and value is not None and value not in valid_options:
        raise ValueError(
            f"Unrecognized value for the {name!r} argument: {value!r}. " f"Expected one of: {sorted(valid_options)}"
        )
    return value
