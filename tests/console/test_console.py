# pylint: disable=redefined-outer-name
"""CLI tests"""

import typing as t

import classlogging
import pytest
from click.testing import CliRunner
from dotenv.main import DotEnv

from cjunct import console, version
from cjunct.config.environment import Env

OptsType = t.Optional[t.List[str]]


class CLIError(Exception):
    """CLI test failure"""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        text: str = f"<{code}>"
        if message:
            text += f" {message}"
        super().__init__(self, text)


class RunnerType(t.Protocol):
    """Protocol for the `runner` fixture return type"""

    def __call__(self, text: str, opts: OptsType = None, global_opts: OptsType = None) -> t.List[str]: ...


def _invoke(*args, **kwargs) -> t.List[str]:
    result = CliRunner(mix_stderr=False).invoke(*args, **kwargs)
    if result.exit_code:
        raise CLIError(code=result.exit_code, message=result.stderr) from None
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
    monkeypatch.setattr(DotEnv, "set_as_environment_variables", _noop)
    monkeypatch.setattr(classlogging, "configure_logging", _noop)

    def run(text: str, opts: OptsType = None, global_opts: OptsType = None) -> t.List[str]:
        return _invoke(console.main, (global_opts or []) + ["run", "-"] + (opts or []), input=text)

    return run


GOOD_WORKFLOW_TEXT: str = """---
actions:
  - type: echo
    message: foo
"""


def test_cli_run(runner: RunnerType) -> None:
    """Default run"""
    assert runner(text=GOOD_WORKFLOW_TEXT) == [
        "[echo-0]  | foo",
        "===============",
        "SUCCESS: echo-0",
    ]


def test_cli_run_display(runner: RunnerType) -> None:
    """Run with overridden display"""
    assert runner(
        text=GOOD_WORKFLOW_TEXT,
        global_opts=["--display", "headers"],
    ) == [
        " ┌─[echo-0]",
        " │ foo",
        " ╵",
        " ✓ SUCCESS: echo-0",
    ]


@pytest.mark.parametrize("strategy", ["free", "sequential", "loose", "strict", "strict-sequential"])
def test_cli_run_explicit_strategy(runner: RunnerType, strategy: str) -> None:
    """Run with overridden strategy"""
    assert runner(
        text=GOOD_WORKFLOW_TEXT,
        opts=["--strategy", strategy],
    ) == [
        "[echo-0]  | foo",
        "===============",
        "SUCCESS: echo-0",
    ]


def test_cli_run_execution_failed(runner: RunnerType) -> None:
    """Catch ExecutionFailed"""
    with pytest.raises(CLIError, match="<1>"):
        runner(text="{actions: [{type: shell, command: foobar}]}")


def test_cli_run_load_error(runner: RunnerType) -> None:
    """Catch LoadError"""
    with pytest.raises(CLIError, match="<102>"):
        runner(text="actions:")


def test_cli_run_integrity_error(runner: RunnerType) -> None:
    """Catch IntegrityError"""
    with pytest.raises(CLIError, match="<103>"):
        runner(text="actions: []")
