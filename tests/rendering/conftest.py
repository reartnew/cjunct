"""Templar fixtures"""

import os

import pytest

from cjunct.rendering import Templar, containers as c


@pytest.fixture
def templar(monkeypatch: pytest.MonkeyPatch) -> Templar:
    """Prepare a standalone templar"""
    monkeypatch.setenv("TEMPLAR_ENVIRONMENT_KEY", "test")
    return Templar(
        outcomes=c.ActionContainingDict(
            {
                "Foo": c.LooseOutcomeDict(
                    {
                        "bar": "ok",
                        "baz qux.fred": "also ok",
                    }
                ),
            }
        ),
        status=c.ActionContainingDict({"Foo": "SUCCESS"}),
        context=c.ContextDict(
            {
                "plugh": "xyzzy",
                "thud": "@{context.waldo}",
                "waldo": "@{context.thud}",
            }
        ),
        environment=c.AttrDict(os.environ),
    )
