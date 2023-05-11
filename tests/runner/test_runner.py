"""Runner public methods tests"""
# pylint: disable=unused-argument

import os
from pathlib import Path
import typing as t

import pytest

import cjunct
from cjunct.strategy import BaseStrategy
from cjunct.exceptions import SourceError


def test_simple_runner_call(runner_context: None) -> None:
    """Check default call"""
    cjunct.Runner().run_sync()


def test_missing_config(tmp_path: Path) -> None:
    """Check default call"""
    os.chdir(tmp_path)
    with pytest.raises(SourceError, match="No config source detected in"):
        cjunct.Runner()


@pytest.mark.parametrize("strategy_class", [cjunct.FreeStrategy, cjunct.SequentialStrategy, cjunct.LooseStrategy])
def test_strategy_runner_call(
    runner_context: None,
    strategy_class: t.Type[BaseStrategy],
    display_collector: t.List[str],
) -> None:
    """Check all strategies"""
    cjunct.Runner(strategy_class=strategy_class).run_sync()
    assert set(display_collector) == {
        "[Foo] | foo",
        "[Bar] | bar",
    }
