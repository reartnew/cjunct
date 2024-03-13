"""Runner call fixtures"""

# pylint: disable=redefined-outer-name

import base64
import typing as t
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from cjunct.config.environment import Env
from cjunct.display.base import BaseDisplay


@pytest.fixture(scope="session", autouse=True)
def disable_env_cache() -> None:
    """Do not cache environment variables values for varying tests"""
    Env.cache_values = False


@pytest.fixture
def display_collector(monkeypatch: pytest.MonkeyPatch) -> t.List[str]:
    """Creates display events list instead of putting them to stdout"""
    results: t.List[str] = []

    # pylint: disable=unused-argument
    def display(self, message: str) -> None:
        results.append(message)

    monkeypatch.setattr(BaseDisplay, "display", display)
    return results


@pytest.fixture(params=["chdir", "env_context_dir", "env_actions_source"])
def runner_good_context(request: SubRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with good sample config files"""
    actions_source_path: Path = tmp_path / "cjunct.yaml"
    actions_source_path.write_bytes(
        b"""---
actions:
  - name: Foo
    type: shell
    command: echo "foo"
  - name: Bar
    type: shell
    command: echo "bar" >&2
    depends_on:
      - Foo
"""
    )
    if request.param == "chdir":
        monkeypatch.chdir(tmp_path)
    elif request.param == "env_context_dir":
        monkeypatch.setenv("CJUNCT_CONTEXT_DIRECTORY", str(tmp_path))
    elif request.param == "env_actions_source":
        monkeypatch.setenv("CJUNCT_ACTIONS_SOURCE_FILE", str(actions_source_path))
    else:
        raise ValueError(request.param)


@pytest.fixture(params=["chdir", "env_context_dir", "env_actions_source"])
def runner_shell_yield_good_context(request: SubRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with good sample config files using shell yield feature"""

    def _str_to_b64(s: str) -> str:
        return base64.b64encode(s.encode()).decode()

    actions_source_path: Path = tmp_path / "cjunct.yaml"
    actions_source_path.write_bytes(
        f"""---
actions:
  - name: Foo
    type: shell
    command: yield_outcome result-key "I am foo" 
  - name: Bar
    type: shell
    command: |
     echo "@{{outcomes.Foo.result-key}}"
     echo "Prefix ##cjunct[yield-outcome-b64 {_str_to_b64('result-key')} {_str_to_b64('bar')}]##"
    depends_on: [Foo]
  - name: Baz
    type: shell
    command: echo "@{{outcomes.Bar.result-key}}" 
    depends_on: [Bar]
""".encode()
    )
    if request.param == "chdir":
        monkeypatch.chdir(tmp_path)
    elif request.param == "env_context_dir":
        monkeypatch.setenv("CJUNCT_CONTEXT_DIRECTORY", str(tmp_path))
    elif request.param == "env_actions_source":
        monkeypatch.setenv("CJUNCT_ACTIONS_SOURCE_FILE", str(actions_source_path))
    else:
        raise ValueError(request.param)


@pytest.fixture
def runner_failing_action_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with sample config files of a failing action"""
    actions_source_path: Path = tmp_path / "cjunct.yaml"
    actions_source_path.write_bytes(
        b"""---
actions:
  - name: Qux
    type: shell
    command: echo "qux" && exit 1
"""
    )
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def runner_failing_warmup_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with sample config files of a failing warmup"""
    actions_source_path: Path = tmp_path / "cjunct.yaml"
    actions_source_path.write_bytes(
        b"""---
actions:
  - name: Baz
    type: shell
    command: echo "##cjunct[yield-outcome-b64 * *]##"
  - name: Qux
    type: shell
    command: echo "@{A.B.C}"
"""
    )
    monkeypatch.chdir(tmp_path)
