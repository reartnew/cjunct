"""Test miscellaneous CLI components"""
# pylint: disable=unused-argument

import pytest

from cjunct.config.constants import C
from cjunct.config.environment import Env
from cjunct.strategy import LooseStrategy, FreeStrategy
from cjunct.display.default import NetPrefixDisplay


def test_invalid_strategy_cli_arg(invalid_strategy_cli_arg: None) -> None:
    """Check error throw for bad CLI strategy arg value"""
    with pytest.raises(ValueError, match="Unrecognized value for the 'strategy' argument"):
        assert C.STRATEGY_CLASS


def test_default_strategy() -> None:
    """Check that default strategy is loose"""
    Env.CJUNCT_STRATEGY_NAME = ""
    assert C.STRATEGY_CLASS is LooseStrategy


def test_valid_strategy_env_var() -> None:
    """Check resolution for good environment strategy variable value"""
    Env.CJUNCT_STRATEGY_NAME = "free"
    assert C.STRATEGY_CLASS is FreeStrategy


def test_invalid_strategy_env_var() -> None:
    """Check error throw for bad environment strategy variable value"""
    Env.CJUNCT_STRATEGY_NAME = "unknown-strategy"
    with pytest.raises(ValueError, match="Invalid strategy name:"):
        assert C.STRATEGY_CLASS


def test_default_display() -> None:
    """Check that default display is net-prefix"""
    Env.CJUNCT_DISPLAY_SOURCE_FILE = ""
    assert C.DISPLAY_CLASS is NetPrefixDisplay
