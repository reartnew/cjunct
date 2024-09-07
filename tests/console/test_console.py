import classlogging
from click.testing import CliRunner
from dotenv.main import DotEnv
import typing as t

from cjunct import console, version
from cjunct.config.environment import Env


def _invoke(*args, **kwargs) -> t.List[str]:
    result = CliRunner(mix_stderr=False).invoke(*args, **kwargs)
    assert not result.exit_code, result.stderr
    return result.stdout.splitlines()


def _noop(*args, **kwargs) -> None:
    return None


def test_cli_version():
    assert _invoke(console.version) == [version.__version__]


def test_cli_env_vars():
    assert _invoke(console.env_vars) == Env.__doc__.splitlines()


def test_cli_run(monkeypatch):
    monkeypatch.setattr(DotEnv, "set_as_environment_variables", _noop)
    monkeypatch.setattr(classlogging, "configure_logging", _noop)
    assert _invoke(console.run, ["-"], input="actions:\n- type: echo\n  message: foo") == [
        "[echo-0]  | foo",
        "===============",
        "SUCCESS: echo-0",
    ]
