"""Runner public methods tests"""

# pylint: disable=unused-argument

import io
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


@pytest.mark.parametrize(
    "strategy_class",
    [
        cjunct.FreeStrategy,
        cjunct.SequentialStrategy,
        cjunct.LooseStrategy,
        cjunct.StrictStrategy,
        cjunct.StrictSequentialStrategy,
    ],
)
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


def test_failing_render(runner_failing_render_context: None) -> None:
    """Check failing render in the runner"""
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_failing_union_render(runner_failing_union_render_context: None) -> None:
    """Check failing union render in the runner"""
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_external_actions(runner_external_actions_context: None) -> None:
    """Check external actions from directories"""
    cjunct.Runner().run_sync()


def test_invalid_action_source_file_via_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check raising SourceError for absent file via CJUNCT_ACTIONS_SOURCE_FILE"""
    monkeypatch.setenv("CJUNCT_ACTIONS_SOURCE_FILE", str(tmp_path / "missing.yaml"))
    with pytest.raises(exceptions.SourceError, match="Pre-configured actions source file does not exist"):
        cjunct.Runner().run_sync()


def test_status_good_substitution(runner_status_substitution_good_context: None) -> None:
    """Check status good substitution"""
    cjunct.Runner().run_sync()


def test_status_bad_substitution(runner_status_substitution_bad_context: None) -> None:
    """Check status bad substitution"""
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_stdin_feed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check actions fed from stdin"""
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(
            """---
actions:
  - name: Foo
    type: shell
    command: pwd
"""
        ),
    )
    monkeypatch.setenv("CJUNCT_ACTIONS_SOURCE_FILE", "-")
    cjunct.Runner().run_sync()


@pytest.mark.asyncio
async def test_docker_good_context(runner_docker_good_context: None, display_collector: t.List[str]) -> None:
    """Check docker shell action step"""
    await cjunct.Runner().run_async()
    assert set(display_collector) == {
        "[Foo]  | bar-baz",
        "============",
        "SUCCESS: Foo",
    }


@pytest.mark.asyncio
async def test_docker_bad_context(runner_docker_bad_context: None) -> None:
    """Check docker shell action step failure"""
    with pytest.raises(exceptions.ExecutionFailed):
        await cjunct.Runner().run_async()


@pytest.mark.asyncio
async def test_docker_bad_auth_context(runner_docker_bad_auth_context: None) -> None:
    """Check docker shell action step auth failure"""
    with pytest.raises(exceptions.ExecutionFailed):
        await cjunct.Runner().run_async()


def test_complex_loose_context(runner_non_releasing_action_context: None) -> None:
    """Test a context where a finished action releases no new actions"""
    cjunct.Runner().run_sync()


def test_empty_echo_context(runner_empty_echo_context: None, display_collector: t.List[str]) -> None:
    """Test empty echo"""
    cjunct.Runner().run_sync()
    assert set(display_collector) == {
        "[Foo]  | ",
        "============",
        "SUCCESS: Foo",
    }


def test_misplaced_disable_context(runner_misplaced_disable_context: None, display_collector: t.List[str]) -> None:
    """Test context with misplaced action disable call"""
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()
    assert (
        "[Foo] !| Action 'Foo' run exception: RuntimeError(\"Action Foo can't be disabled due to its status: RUNNING\")"
        in display_collector
    )


def test_interaction_context(runner_interaction_context: None, display_collector: t.List[str]) -> None:
    """Test interaction context"""
    cjunct.Runner().run_sync()
    assert display_collector == [
        "============",
        "SUCCESS: Foo",
        "OMITTED: Bar",
        "OMITTED: Baz",
    ]
