# pylint: disable=redefined-outer-name
"""CLI tests"""

import typing as t

import classlogging
import pytest
from click.testing import CliRunner
from dotenv.main import DotEnv

from cjunct import console, version
from cjunct.config.environment import Env


class RunnerType(t.Protocol):
    """Protocol for the `runner` fixture return type"""

    def __call__(self, *args: str, global_flags: t.Optional[t.List[str]] = None) -> t.List[str]: ...


def _invoke(*args, **kwargs) -> t.List[str]:
    result = CliRunner(mix_stderr=False).invoke(*args, **kwargs)
    assert not result.exit_code, result.stderr
    return result.stdout.splitlines()


def _noop(*args, **kwargs) -> None:  # pylint: disable=unused-argument
    return None


def test_cli_version() -> None:
    """Check version command"""
    assert _invoke(console.main, ["info", "version"]) == [version.__version__]


def test_cli_env_vars() -> None:
    """Check env vars command"""
    doc: str = t.cast(str, Env.__doc__)
    assert _invoke(console.main, ["info", "env-vars"]) == doc.splitlines()


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch) -> RunnerType:
    """Setup test runner fed from stdin"""
    wf_text: str = """---
    actions:
      - type: echo
        message: foo
    """
    monkeypatch.setattr(DotEnv, "set_as_environment_variables", _noop)
    monkeypatch.setattr(classlogging, "configure_logging", _noop)

    def run(*args: str, global_flags: t.Optional[t.List[str]] = None) -> t.List[str]:
        return _invoke(console.main, (global_flags or []) + ["run", "-"] + list(args), input=wf_text)

    return run


def test_cli_run(runner: RunnerType) -> None:
    """Default run"""
    assert runner() == [
        "[echo-0]  | foo",
        "===============",
        "SUCCESS: echo-0",
    ]


def test_cli_run_display(runner: RunnerType) -> None:
    """Run with overridden display"""
    assert runner(global_flags=["--display", "headers"]) == [
        " ┌─[echo-0]",
        " │ foo",
        " ╵",
        " ✓ SUCCESS: echo-0",
    ]


@pytest.mark.parametrize("strategy", ["free", "sequential", "loose", "strict", "strict-sequential"])
def test_cli_run_explicit_strategy(runner: RunnerType, strategy: str) -> None:
    """Run with overridden strategy"""
    assert runner("--strategy", strategy) == [
        "[echo-0]  | foo",
        "===============",
        "SUCCESS: echo-0",
    ]
