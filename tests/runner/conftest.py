"""Runner call fixtures"""

# pylint: disable=redefined-outer-name,unused-argument

import base64
import textwrap
import typing as t
from pathlib import Path

import aiodocker
import pytest
import pytest_asyncio
from _pytest.fixtures import SubRequest

from cjunct.config.environment import Env
from cjunct.config.constants import C
from cjunct.display.default import DefaultDisplay

CtxFactoryType = t.Callable[[str], Path]


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

    # pylint: disable=unused-argument
    def _run_dialog(
        cls,
        displayed_action_names: t.List[str],
        default_selected_action_names: t.List[str],
    ) -> t.List[str]:
        return default_selected_action_names[:1]

    monkeypatch.setattr(DefaultDisplay, "display", display)
    monkeypatch.setattr(DefaultDisplay, "_run_dialog", _run_dialog)
    return results


@pytest.fixture
def ctx_from_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CtxFactoryType:
    """Context factory"""

    def make(data: str) -> Path:
        actions_source_path: Path = tmp_path / "cjunct.yaml"
        actions_source_path.write_bytes(textwrap.dedent(data).encode())
        monkeypatch.chdir(tmp_path)
        return actions_source_path

    return make


@pytest.fixture
def actions_definitions_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Add actions definitions from directories"""
    actions_class_definitions_base_path: Path = Path(__file__).parent / "extension" / "modules" / "actions"
    monkeypatch.setenv(
        name="CJUNCT_ACTIONS_CLASS_DEFINITIONS_DIRECTORY",
        value=",".join(str(actions_class_definitions_base_path / sub_dir) for sub_dir in ("first", "second")),
    )


@pytest.fixture(params=["chdir", "env_workflow"])
def runner_good_context(ctx_from_text: CtxFactoryType, request: SubRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with good sample workflow files"""
    actions_source_path: Path = ctx_from_text(
        """
        actions:
          - name: Foo
            type: shell
            command: echo "foo"
          - name: Bar
            type: shell
            command: echo "bar" >&2
            expects:
              - Foo
        """
    )
    if request.param == "chdir":
        monkeypatch.chdir(actions_source_path.parent)
    elif request.param == "env_workflow":
        monkeypatch.setenv("CJUNCT_WORKFLOW_FILE", str(actions_source_path))
    else:
        raise ValueError(request.param)


@pytest.fixture(params=["chdir", "env_workflow"])
def runner_shell_yield_good_context(request: SubRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with good sample workflow files using shell yield feature"""

    def _str_to_b64(s: str) -> str:
        return base64.b64encode(s.encode()).decode()

    actions_source_path: Path = tmp_path / "cjunct.yaml"
    actions_source_path.write_bytes(
        f"""---
context:
    bar_prefix: Prefix
actions:
  - name: Foo
    type: shell
    command: yield_outcome result_key "I am foo" 
  - name: Bar
    type: shell
    command: |
     echo "@{{outcomes.Foo.result_key}}"
     echo "@{{context.bar_prefix}} ##cjunct[yield-outcome-b64 {_str_to_b64('result_key')} {_str_to_b64('bar')}]##"
    expects: Foo
  - name: Baz
    type: shell
    command: echo "@{{outcomes.Bar.result_key}}"
    expects: Bar
  - name: Pivoslav
    type: shell
    command: skip
""".encode()
    )
    if request.param == "chdir":
        monkeypatch.chdir(tmp_path)
    elif request.param == "env_workflow":
        monkeypatch.setenv("CJUNCT_WORKFLOW_FILE", str(actions_source_path))
    else:
        raise ValueError(request.param)


@pytest.fixture
def runner_failing_action_context(ctx_from_text: CtxFactoryType) -> None:
    """Prepare a directory with sample workflow files of a failing action"""
    ctx_from_text(
        """
        actions:
          - name: Qux
            type: shell
            command: echo "qux" && exit 1
        """
    )


@pytest.fixture
def runner_failing_render_context(ctx_from_text: CtxFactoryType) -> None:
    """Prepare a directory with sample workflow files of a failing render"""
    ctx_from_text(
        """
        actions:
          - name: Baz
            type: shell
            command: echo "##cjunct[yield-outcome-b64 + +]##"
          - name: Qux
            type: shell
            command: echo "@{A.B.C}"
          - name: Fred
            type: shell
            command: echo "@{outcomes.not-enough-parts}"
          - name: Egor
            type: shell
            command: echo "@{outcomes.Baz.non-existent}"
          - name: Kuzma
            type: shell
            command: echo "##cjunct[what-is-this-expression]##"
        """
    )


@pytest.fixture
def runner_external_actions_context(ctx_from_text: CtxFactoryType, actions_definitions_directory: None) -> None:
    """Prepare a directory with sample workflow files using external actions from directories"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: debug
            message: Hi
        """
    )


@pytest.fixture
def runner_status_substitution_good_context(ctx_from_text: CtxFactoryType) -> None:
    """Prepare a directory with sample workflow files testing status good substitution"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: shell
            command: |
              [ "@{status.Foo}" = "PENDING" ] || exit 1
        """
    )


@pytest.fixture
def runner_status_substitution_bad_context(ctx_from_text: CtxFactoryType) -> None:
    """Prepare a directory with sample workflow files testing status bad substitution"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: shell
            command: echo "@{status.too.may.parts}"
        """
    )


@pytest.fixture
def runner_failing_union_render_context(ctx_from_text: CtxFactoryType, actions_definitions_directory: None) -> None:
    """Prepare a directory with sample workflow files using external actions from directories with union render types"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: union-arg-action
            message: "@{some.failing.expression}"
        """
    )


@pytest_asyncio.fixture
async def check_docker() -> None:
    """Skip if no docker context is available"""
    try:
        async with aiodocker.Docker():
            pass
    except Exception as e:
        pytest.skip(f"Unable to load docker context: {e!r}")


@pytest_asyncio.fixture
async def runner_docker_good_context(check_docker: None, ctx_from_text: CtxFactoryType, tmp_path: Path) -> None:
    """Docker-shell good context"""
    tmp_file_to_bind: Path = tmp_path / "bind_file.txt"
    tmp_file_to_bind.write_bytes(b"bar")
    ctx_from_text(
        f"""
        actions:
          - type: docker-shell
            name: Foo
            image: alpine:latest
            command: |
              cat /tmp/bind_file.txt
              printf "-"
              cat /tmp/bind_text.txt
            pull: False
            bind:
              - src: {tmp_file_to_bind}
                dest: /tmp/bind_file.txt
              - contents: baz
                dest: /tmp/bind_text.txt
        """
    )


@pytest_asyncio.fixture
async def runner_docker_bad_context(check_docker: None, ctx_from_text: CtxFactoryType) -> None:
    """Docker-shell bad context"""
    ctx_from_text(
        """
        actions:
          - type: docker-shell
            name: Foo
            image: alpine:latest
            command: no-such-command
        """
    )


@pytest_asyncio.fixture
async def runner_docker_bad_auth_context(check_docker: None, ctx_from_text: CtxFactoryType) -> None:
    """Docker-shell bad auth context"""
    ctx_from_text(
        """
        actions:
          - type: docker-shell
            name: Foo
            image: alpine:latest
            command: pwd
            pull: True
            auth:
              username: foo
              password: bar
              hostname: baz
        """
    )


@pytest.fixture
def runner_non_releasing_action_context(ctx_from_text: CtxFactoryType, actions_definitions_directory: None) -> None:
    """Prepare a context where a finished action releases no new actions"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            description: Finishes very soon, but releases nothing
            type: sleep
            duration: 0.0
          - name: Bar
            type: sleep
            duration: 0.1
          - name: Baz
            type: echo
            message: Done
            expects: Bar
        """
    )


@pytest.fixture
def runner_empty_echo_context(ctx_from_text: CtxFactoryType) -> None:
    """Prepare a context with empty echo message"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: echo
            message: ""
        """
    )


@pytest.fixture
def runner_misplaced_disable_context(ctx_from_text: CtxFactoryType, actions_definitions_directory: None) -> None:
    """Prepare a context with misplaced action disable call"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: misplaced-disable
        """
    )


@pytest.fixture
def runner_interaction_context(
    ctx_from_text: CtxFactoryType,
    actions_definitions_directory: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prepare an interaction context"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: noop
          - name: Bar
            type: noop
            selectable: False
          - name: Baz
            type: noop
        """
    )
    monkeypatch.setattr(C, "INTERACTIVE_MODE", True)
