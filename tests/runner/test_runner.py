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
from cjunct.config.environment import Env
from cjunct.strategy import BaseStrategy
from .types import RunFactoryType, CtxFactoryType


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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check all strategies"""
    monkeypatch.setattr(Env, "CJUNCT_STRATEGY_NAME", strategy_class.NAME)
    cjunct.Runner().run_sync()
    assert set(display_collector) == {
        "[Foo]  | foo",
        "[Bar] *| bar",
        "============",
        "SUCCESS: Foo",
        "SUCCESS: Bar",
    }


def test_failing_actions(run_text: RunFactoryType) -> None:
    """Check failing action in the runner"""
    with pytest.raises(exceptions.ExecutionFailed):
        run_text(
            """
            actions:
              - name: Qux
                type: shell
                command: echo "qux" && exit 1
            """
        )


def test_failing_render(run_text: RunFactoryType) -> None:
    """Check failing render in the runner"""
    with pytest.raises(exceptions.ExecutionFailed):
        run_text(
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


def test_failing_union_render(run_text: RunFactoryType) -> None:
    """Check failing union render in the runner"""
    with pytest.raises(exceptions.ExecutionFailed):
        run_text(
            """
            actions:
              - name: Foo
                type: union-arg-action
                message: "@{some.failing.expression}"
            """
        )


def test_external_actions(run_text: RunFactoryType) -> None:
    """Check external actions from directories"""
    run_text(
        """
        actions:
          - name: Foo
            type: debug
            message: Hi
        """
    )


def test_invalid_action_source_file_via_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check raising SourceError for absent file via CJUNCT_WORKFLOW_FILE"""
    monkeypatch.setenv("CJUNCT_WORKFLOW_FILE", str(tmp_path / "missing.yaml"))
    with pytest.raises(exceptions.SourceError, match="Given workflow file does not exist"):
        cjunct.Runner().run_sync()


def test_status_good_substitution(run_text: RunFactoryType) -> None:
    """Check status good substitution"""
    run_text(
        """
        actions:
          - name: Foo
            type: shell
            command: |
              [ "@{status.Foo}" = "PENDING" ] || exit 1
        """
    )


def test_status_bad_substitution(run_text: RunFactoryType) -> None:
    """Check status bad substitution"""
    with pytest.raises(exceptions.ExecutionFailed):
        run_text(
            """
            actions:
              - name: Foo
                type: shell
                command: echo "@{status.too.may.parts}"
            """
        )


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
    assert display_collector == [
        "[Foo]  | bar-baz",
        "============",
        "SUCCESS: Foo",
    ]


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


def test_complex_loose_context(run_text: RunFactoryType) -> None:
    """Test a context where a finished action releases no new actions"""
    run_text(
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


def test_empty_echo_context(run_text: RunFactoryType) -> None:
    """Test empty echo"""
    output = run_text(
        """
        actions:
          - name: Foo
            type: echo
            message: ""
        """
    )
    assert output == [
        "[Foo]  | ",
        "============",
        "SUCCESS: Foo",
    ]


def test_misplaced_disable_context(
    run_text: RunFactoryType,
    display_collector: t.List[str],
) -> None:
    """Test context with misplaced action disable call"""

    with pytest.raises(exceptions.ExecutionFailed):
        run_text(
            """
            actions:
              - name: Foo
                type: misplaced-disable
            """
        )
    assert (
        "[Foo] !| Action 'Foo' run exception: RuntimeError(\"Action Foo can't be disabled due to its status: RUNNING\")"
        in display_collector
    )


def test_interaction_context(
    run_text: RunFactoryType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test interaction context"""
    monkeypatch.setattr(C, "INTERACTIVE_MODE", True)
    output = run_text(
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
    assert output == [
        "============",
        "SUCCESS: Foo",
        "OMITTED: Bar",
        "OMITTED: Baz",
    ]


def test_complex_vars_context(run_text: RunFactoryType) -> None:
    """Test complex vars context"""
    output = run_text(
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
    assert output == [
        "[Test]  | Hello world!",
        "=============",
        "SUCCESS: Test",
    ]


def test_runner_with_shell_env_inheritance(
    run_text: RunFactoryType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check environment inheritance for shell action"""
    monkeypatch.setenv("INHERITED_VAR_NAME", "inherited var value")
    run_text(
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


def test_runner_accepts_object_template(run_text: RunFactoryType) -> None:
    """Check possibility for passing object template to an action"""
    output = run_text(
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
    assert output == [
        "[Foo]  | FOO",
        "============",
        "SUCCESS: Foo",
    ]


def test_broken_object_template(run_text: RunFactoryType) -> None:
    """Check bad object templates"""
    with pytest.raises(exceptions.ExecutionFailed):
        run_text(
            """
            ---
            actions:
              - name: Foo
                type: shell
                environment: !@ ctx.shell_env
                command: !@ ctx.shell_command
            """
        )


def test_runner_enum_templates(run_text: RunFactoryType) -> None:
    """Check possibility for passing string template to Enum args"""
    run_text(
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


def test_runner_lazy_proxy_unwrapping(run_text: RunFactoryType) -> None:
    """Check that lazy proxies are properly unwrapped"""
    output = run_text(
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
    assert output == [
        "[Foo]  | Foo Bar",
        "============",
        "SUCCESS: Foo",
    ]


def test_implicit_naming(run_text: RunFactoryType) -> None:
    """Check automatically assigned action names"""
    output = run_text(
        """
        ---
        actions:
          - type: shell
            command: echo Foo
        """
    )
    assert output == [
        "[shell-0]  | Foo",
        "================",
        "SUCCESS: shell-0",
    ]


def test_low_severity(run_text: RunFactoryType) -> None:
    """Check that low severity action does not stop the execution"""
    output = run_text(
        """
        ---
        actions:
          - type: shell
            command: echo Foo && exit 1
            severity: low
        """
    )
    assert output == [
        "[shell-0]  | Foo",
        "          !| Exit code: 1",
        "================",
        "WARNING: shell-0",
    ]


def test_render_wrong_type(
    run_text: RunFactoryType,
    display_collector: t.List[str],
) -> None:
    """Check late render type mismatch"""

    with pytest.raises(exceptions.ExecutionFailed):
        run_text(
            """
            ---
            actions:
              - type: shell
                environment: !@ |
                  {"Foo": None}
                command: echo Foo
            """
        )
    # Can't check exactly due to different representations of the Optional in different python versions
    assert any(
        k.startswith(
            "[shell-0] !| Action 'shell-0' rendering failed: Unrecognized 'environment' "
            "content type: typing.Dict[str, NoneType]"
        )
        for k in display_collector
    )
