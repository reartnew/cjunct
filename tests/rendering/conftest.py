# pylint: disable=redefined-outer-name
"""Templar fixtures"""

import typing as t

import pytest

from cjunct.config.environment import Env
from cjunct.rendering import Templar


@pytest.fixture
def templar_factory(monkeypatch: pytest.MonkeyPatch) -> t.Callable[[], Templar]:
    """Prepare a standalone templar"""
    monkeypatch.setenv("TEMPLAR_ENVIRONMENT_KEY", "test")

    def make():
        return Templar(
            outcomes_map={
                "Foo": {
                    "bar": "ok",
                    "baz qux.fred": "also ok",
                },
            },
            action_states={"Foo": "SUCCESS"},
            context_map={
                "plugh": "xyzzy",
                "waldo": "@{context.thud}",
                "thud": "@{environment.TEMPLAR_ENVIRONMENT_KEY}",
                "intval": 10,
                "cycle_1": "@{context.cycle_2}",
                "cycle_2": "@{context.cycle_1}",
                "dictData": [
                    {
                        "a": "b",
                    }
                ],
                "deepRenderData": {
                    "foo": "This is a @{context.waldo}",
                    "bar": ["a", "@{context.intval * 2}"],
                    "baz": "@{context.missingStuff}",
                },
            },
        )

    return make


@pytest.fixture
def templar(templar_factory: t.Callable[[], Templar]) -> Templar:
    """Loose (default) templar"""
    return templar_factory()


@pytest.fixture
def strict_templar(templar_factory: t.Callable[[], Templar], monkeypatch: pytest.MonkeyPatch) -> Templar:
    """Strict templar"""
    monkeypatch.setattr(Env, "CJUNCT_STRICT_OUTCOMES_RENDERING", True)
    return templar_factory()
