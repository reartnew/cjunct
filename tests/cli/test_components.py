"""Test miscellaneous CLI components"""
# pylint: disable=unused-argument

import pytest

from cjunct.config.constants import C


def test_invalid_strategy_cli_arg(invalid_strategy_cli_arg: None) -> None:
    """Check error throw for bad CLI strategy arg value"""

    with pytest.raises(ValueError, match="Unrecognized value for the 'strategy' argument"):
        assert C.STRATEGY_CLASS
