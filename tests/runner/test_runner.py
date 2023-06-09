"""Runner public methods tests"""
# pylint: disable=unused-argument

import os
import typing as t
from pathlib import Path

import pytest

import cjunct
from cjunct import exceptions
from cjunct.strategy import BaseStrategy


def test_simple_runner_call(runner_context: None) -> None:
    """Check default call"""
    cjunct.Runner().run_sync()


def test_runner_multiple_run(runner_context: None) -> None:
    """Check default call"""
    runner = cjunct.Runner()
    runner.run_sync()
    with pytest.raises(RuntimeError):
        runner.run_sync()


def test_status_banners(runner_context: None) -> None:
    """Check status banners"""
    runner = cjunct.Runner()
    assert runner.get_status_banner() == ""
    runner.run_sync()
    assert runner.get_status_banner() == "SUCCESS: Foo\nSUCCESS: Bar"


def test_not_found_config(tmp_path: Path) -> None:
    """Empty source directory"""
    os.chdir(tmp_path)
    with pytest.raises(exceptions.SourceError, match="No config source detected in"):
        cjunct.Runner().run_sync()


def test_non_existent_config(tmp_path: Path) -> None:
    """No config file with given name"""
    os.chdir(tmp_path)
    with pytest.raises(exceptions.LoadError, match="Config file not found"):
        cjunct.Runner(config=tmp_path / "network.xml").run_sync()


def test_unrecognized_config(tmp_path: Path) -> None:
    """Unknown config file format"""
    os.chdir(tmp_path)
    with pytest.raises(exceptions.SourceError, match="Unrecognized source"):
        cjunct.Runner(config=tmp_path / "network.foo").run_sync()


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
