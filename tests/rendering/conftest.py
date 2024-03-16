"""Templar fixtures"""

import pytest

from cjunct.rendering import Templar


@pytest.fixture
def templar(monkeypatch: pytest.MonkeyPatch) -> Templar:
    """Prepare a standalone templar"""
    monkeypatch.setenv("TEMPLAR_ENVIRONMENT_KEY", "test")
    return Templar(
        outcomes_getter={
            "Foo": {
                "bar": "ok",
                "baz qux.fred": "also ok",
            },
        }.get,
        status_getter={"Foo": "SUCCESS"}.get,
        raw_context_getter={
            "plugh": "xyzzy",
            "thud": "@{context.waldo}",
            "waldo": "@{context.thud}",
        }.get,
    )
