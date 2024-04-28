# pylint: disable=unused-argument,redefined-outer-name,missing-function-docstring
"""Display tests"""

import io
import typing as t

import pytest

from cjunct import exceptions, Runner
from cjunct.display.base import BaseDisplay


class BaseBadDisplay(BaseDisplay):
    """Bad displays base"""

    FAILURES: t.Set[str]
    METHOD_FAILURES_TO_CHECK: t.Set[str] = {
        "emit_action_message",
        "emit_action_error",
        "on_finish",
        "on_action_start",
        "on_action_finish",
    }

    @classmethod
    def make_failure(cls, name: str) -> t.Callable:
        def failure(self, *args, **kwargs) -> t.Any:
            cls.FAILURES.add(name)
            raise RuntimeError

        return failure


@pytest.fixture
def bad_display_class() -> t.Type[BaseBadDisplay]:
    class BadDisplay(BaseBadDisplay):
        """A display incapable of doing anything"""

        FAILURES: t.Set[str] = set()

    for method_name in BaseBadDisplay.METHOD_FAILURES_TO_CHECK:
        setattr(BadDisplay, method_name, BadDisplay.make_failure(method_name))

    return BadDisplay


def test_bad_display(bad_display_class: t.Type[BaseBadDisplay]):
    """Check that a bad display does not interrupt execution"""
    source = io.StringIO(
        """
        actions:
          - name: foo
            type: echo
            message: test
          - name: bar
            type: shell
            command: baz
        """
    )
    runner = Runner(source=source, display_class=bad_display_class)
    with pytest.raises(exceptions.ExecutionFailed):
        runner.run_sync()
    assert bad_display_class.FAILURES == BaseBadDisplay.METHOD_FAILURES_TO_CHECK
