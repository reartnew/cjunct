"""CLI components tests fixtures"""

import typing as t
from contextlib import contextmanager

import pytest

from cjunct.config.constants.cli import CLI_PARAMS


@contextmanager
def _cli_arg(name: str, value: str) -> t.Generator[None, None, None]:
    """Temporarily set CLI argument"""
    sentinel = object()
    old_val = CLI_PARAMS.get(name, sentinel)
    CLI_PARAMS[name] = value
    yield
    del CLI_PARAMS[name]
    if old_val is not sentinel:
        CLI_PARAMS[name] = old_val


@pytest.fixture
def invalid_strategy_cli_arg() -> t.Generator[None, None, None]:
    """Set invalid strategy CLI arg"""
    with _cli_arg(name="strategy", value="unknown-strategy"):
        yield
