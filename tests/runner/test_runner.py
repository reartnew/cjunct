"""Runner public methods tests"""

# pylint: disable=unused-argument

import io
import typing as t
from pathlib import Path

import pytest

import cjunct
from cjunct import exceptions
from cjunct.actions.base import ActionStatus
from cjunct.config.constants import C
from cjunct.strategy import BaseStrategy

CtxFactoryType = t.Callable[[str], Path]


def test_simple_runner_call(runner_good_context: None) -> None:
    """Check default call"""
    cjunct.Runner().run_sync()


def test_yield_good_call(runner_shell_yield_good_context: None) -> None:
    """Check yield integration"""
    runner = cjunct.Runner()
    runner.run_sync()
    assert {k.name: k.status for k in runner.workflow.values()} == {
        "Foo": ActionStatus.SUCCESS,
        "Bar": ActionStatus.SUCCESS,
        "Baz": ActionStatus.SUCCESS,
        "Pivoslav": ActionStatus.SKIPPED,
    }


def test_runner_multiple_run(runner_good_context: None) -> None:
    """Check default call"""
    runner = cjunct.Runner()
    runner.run_sync()
    with pytest.raises(RuntimeError):
        runner.run_sync()


def test_not_found_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty source directory"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(exceptions.SourceError, match="No workflow source detected in"):
        cjunct.Runner().run_sync()


def test_multiple_found_workflows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ambiguous source directory"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cjunct.yml").touch()
    (tmp_path / "cjunct.yaml").touch()
    with pytest.raises(exceptions.SourceError, match="Multiple workflow sources detected in"):
        cjunct.Runner().run_sync()


def test_non_existent_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No workflow file with given name"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(exceptions.LoadError, match="Workflow file not found"):
        cjunct.Runner(source=tmp_path / "cjunct.yml").run_sync()


def test_unrecognized_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown workflow file format"""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(exceptions.SourceError, match="Unrecognized source"):
        cjunct.Runner(source=tmp_path / "wf.foo").run_sync()


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


def test_failing_actions(ctx_from_text: CtxFactoryType) -> None:
    """Check failing action in the runner"""
    ctx_from_text(
        """
        actions:
          - name: Qux
            type: shell
            command: echo "qux" && exit 1
        """
    )
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_failing_render(ctx_from_text: CtxFactoryType) -> None:
    """Check failing render in the runner"""
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
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_failing_union_render(
    ctx_from_text: CtxFactoryType,
    actions_definitions_directory: None,
) -> None:
    """Check failing union render in the runner"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: union-arg-action
            message: "@{some.failing.expression}"
        """
    )
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_external_actions(
    ctx_from_text: CtxFactoryType,
    actions_definitions_directory: None,
) -> None:
    """Check external actions from directories"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: debug
            message: Hi
        """
    )
    cjunct.Runner().run_sync()


def test_invalid_action_source_file_via_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check raising SourceError for absent file via CJUNCT_WORKFLOW_FILE"""
    monkeypatch.setenv("CJUNCT_WORKFLOW_FILE", str(tmp_path / "missing.yaml"))
    with pytest.raises(exceptions.SourceError, match="Given workflow file does not exist"):
        cjunct.Runner().run_sync()


def test_status_good_substitution(ctx_from_text: CtxFactoryType) -> None:
    """Check status good substitution"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: shell
            command: |
              [ "@{status.Foo}" = "PENDING" ] || exit 1
        """
    )
    cjunct.Runner().run_sync()


def test_status_bad_substitution(ctx_from_text: CtxFactoryType) -> None:
    """Check status bad substitution"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: shell
            command: echo "@{status.too.may.parts}"
        """
    )
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
    monkeypatch.setenv("CJUNCT_WORKFLOW_FILE", "-")
    cjunct.Runner().run_sync()


@pytest.mark.asyncio
async def test_docker_good_context(
    check_docker: None,
    ctx_from_text: CtxFactoryType,
    tmp_path: Path,
    display_collector: t.List[str],
) -> None:
    """Check docker shell action step"""
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
    await cjunct.Runner().run_async()
    assert set(display_collector) == {
        "[Foo]  | bar-baz",
        "============",
        "SUCCESS: Foo",
    }


@pytest.mark.asyncio
async def test_docker_bad_context(
    check_docker: None,
    ctx_from_text: CtxFactoryType,
) -> None:
    """Check docker shell action step failure"""
    ctx_from_text(
        """
        actions:
          - type: docker-shell
            name: Foo
            image: alpine:latest
            command: no-such-command
        """
    )
    with pytest.raises(exceptions.ExecutionFailed):
        await cjunct.Runner().run_async()


@pytest.mark.asyncio
async def test_docker_bad_auth_context(
    check_docker: None,
    ctx_from_text: CtxFactoryType,
) -> None:
    """Check docker shell action step auth failure"""
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
    with pytest.raises(exceptions.ExecutionFailed):
        await cjunct.Runner().run_async()


def test_complex_loose_context(
    ctx_from_text: CtxFactoryType,
    actions_definitions_directory: None,
) -> None:
    """Test a context where a finished action releases no new actions"""
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
    cjunct.Runner().run_sync()


def test_empty_echo_context(
    ctx_from_text: CtxFactoryType,
    display_collector: t.List[str],
) -> None:
    """Test empty echo"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: echo
            message: ""
        """
    )
    cjunct.Runner().run_sync()
    assert set(display_collector) == {
        "[Foo]  | ",
        "============",
        "SUCCESS: Foo",
    }


def test_misplaced_disable_context(
    ctx_from_text: CtxFactoryType,
    actions_definitions_directory: None,
    display_collector: t.List[str],
) -> None:
    """Test context with misplaced action disable call"""
    ctx_from_text(
        """
        actions:
          - name: Foo
            type: misplaced-disable
        """
    )
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()
    assert (
        "[Foo] !| Action 'Foo' run exception: RuntimeError(\"Action Foo can't be disabled due to its status: RUNNING\")"
        in display_collector
    )


def test_interaction_context(
    ctx_from_text: CtxFactoryType,
    actions_definitions_directory: None,
    monkeypatch: pytest.MonkeyPatch,
    display_collector: t.List[str],
) -> None:
    """Test interaction context"""
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
    cjunct.Runner().run_sync()
    assert display_collector == [
        "============",
        "SUCCESS: Foo",
        "OMITTED: Bar",
        "OMITTED: Baz",
    ]


def test_complex_vars_context(
    ctx_from_text: CtxFactoryType,
    display_collector: t.List[str],
) -> None:
    """Test complex vars context"""
    ctx_from_text(
        """
        ---
        context:
          first_nested_data:
            first_word: Hello
          second_nested_data:
            second_word: world!
          merged_data: !@ |
            {
              **ctx.first_nested_data,
              **ctx.second_nested_data,
            }
        actions:
          - name: Test
            type: echo
            message: "@{context.merged_data.first_word} @{context.merged_data.second_word}"
        """
    )
    cjunct.Runner().run_sync()
    assert display_collector == [
        "[Test]  | Hello world!",
        "=============",
        "SUCCESS: Test",
    ]


def test_runner_with_shell_env_inheritance(
    ctx_from_text: CtxFactoryType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check environment inheritance for shell action"""
    monkeypatch.setenv("INHERITED_VAR_NAME", "inherited var value")
    ctx_from_text(
        """
        ---
        actions:
          - name: Foo
            type: shell
            environment:
              LOCAL_VAR_NAME: local var value
            command: |
              [ "$LOCAL_VAR_NAME" = "local var value" ] || exit 1
              [ "$INHERITED_VAR_NAME" = "inherited var value" ] || exit 2
        """
    )
    cjunct.Runner().run_sync()


def test_runner_accepts_object_template(
    ctx_from_text: CtxFactoryType,
    display_collector: t.List[str],
) -> None:
    """Check possibility for passing object template to an action"""
    ctx_from_text(
        """
        ---
        context:
          shell_env:
            B: F
            A: O
            R: O
          shell_command: echo $B$A$R
          
        actions:
          - name: Foo
            type: shell
            environment: !@ ctx.shell_env
            command: !@ ctx.shell_command
        """
    )
    cjunct.Runner().run_sync()
    assert display_collector == [
        "[Foo]  | FOO",
        "============",
        "SUCCESS: Foo",
    ]


def test_broken_object_template(
    ctx_from_text: CtxFactoryType,
    display_collector: t.List[str],
) -> None:
    """Check bad object templates"""
    ctx_from_text(
        """
        ---
        actions:
          - name: Foo
            type: shell
            environment: !@ ctx.shell_env
            command: !@ ctx.shell_command
        """
    )
    with pytest.raises(exceptions.ExecutionFailed):
        cjunct.Runner().run_sync()


def test_runner_enum_templates(
    ctx_from_text: CtxFactoryType,
    actions_definitions_directory: None,
) -> None:
    """Check possibility for passing string template to Enum args"""
    ctx_from_text(
        """
        ---
        actions:
          - name: Foo
            type: enum-eater
            food: "@{ 'Foo' }"
          - name: Bar
            type: enum-eater
            food: "Bar"
        """
    )
    cjunct.Runner().run_sync()


def test_runner_lazy_proxy_unwrapping(
    ctx_from_text: CtxFactoryType,
    display_collector: t.List[str],
    actions_definitions_directory: None,
) -> None:
    """Check that lazy proxies are properly unwrapped"""
    ctx_from_text(
        """
        ---
        context:
          env: !@ '{"Foo": "Bar"}'
        actions:
          - name: Foo
            type: shell
            environment: !@ ctx.env
            command: echo Foo $Foo
        """
    )
    cjunct.Runner().run_sync()
    assert display_collector == [
        "[Foo]  | Foo Bar",
        "============",
        "SUCCESS: Foo",
    ]


def test_implicit_naming(
    ctx_from_text: CtxFactoryType,
    display_collector: t.List[str],
) -> None:
    """Check automatically assigned action names"""
    ctx_from_text(
        """
        ---
        actions:
          - type: shell
            command: echo Foo
        """
    )
    cjunct.Runner().run_sync()
    assert display_collector == [
        "[shell-0]  | Foo",
        "================",
        "SUCCESS: shell-0",
    ]
