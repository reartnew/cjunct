"""Runner public methods tests"""

# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest

import cjunct
from cjunct import exceptions
from cjunct.strategy import BaseStrategy


def test_simple_runner_call(runner_good_context: None) -> None:
    """Check default call"""
    cjunct.Runner().run_sync()


def test_yield_good_call(runner_shell_yield_good_context: None) -> None:
    """Check yield integration"""
    cjunct.Runner().run_sync()


def test_runner_multiple_run(runner_good_context: None) -> None:
    """Check default call"""
    runner = cjunct.Runner()
    runner.run_sync()
    with pytest.raises(RuntimeError):
        runner.run_sync()


def test_not_found_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty source directory"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(exceptions.SourceError, match="No config source detected in"):
        cjunct.Runner().run_sync()


def test_multiple_found_configs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ambiguous source directory"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cjunct.yml").touch()
    (tmp_path / "cjunct.yaml").touch()
    with pytest.raises(exceptions.SourceError, match="Multiple config sources detected in"):
        cjunct.Runner().run_sync()


def test_non_existent_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No config file with given name"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(exceptions.LoadError, match="Config file not found"):
        cjunct.Runner(config=tmp_path / "cjunct.yml").run_sync()


def test_unrecognized_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown config file format"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(exceptions.SourceError, match="Unrecognized source"):
        cjunct.Runner(config=tmp_path / "network.foo").run_sync()


@pytest.mark.parametrize("strategy_class", [cjunct.FreeStrategy, cjunct.SequentialStrategy, cjunct.LooseStrategy])
def test_strategy_runner_call(
    runner_good_context: None,
    strategy_class: t.Type[BaseStrategy],
    display_collector: t.List[str],
) -> None:
    """Check all strategies"""
    cjunct.Runner(strategy_class=strategy_class).run_sync()
    assert set(display_collector) == {
        "[Foo]  | foo",
        "[Bar] *| bar",
        "============",
        "SUCCESS: Foo",
        "SUCCESS: Bar",
    }


def test_failing_actions(runner_failing_action_context: None) -> None:
    """Check failing action in the runner"""
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_failing_warmup(runner_failing_warmup_context: None) -> None:
    """Check failing warmup in the runner"""
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_invalid_action_source_file_via_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check raising SourceError for absent file via CJUNCT_ACTIONS_SOURCE_FILE"""
    monkeypatch.setenv("CJUNCT_ACTIONS_SOURCE_FILE", str(tmp_path / "missing.yaml"))
    with pytest.raises(exceptions.SourceError, match="Pre-configured actions source file does not exist"):
        cjunct.Runner().run_sync()
