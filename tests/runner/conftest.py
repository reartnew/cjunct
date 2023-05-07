"""Runner call fixtures"""
# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest

from cjunct.display import BaseDisplay


@pytest.fixture
def display_collector(monkeypatch: pytest.MonkeyPatch) -> t.List[str]:
    """Creates display events list instead of putting them to stdout"""
    results: t.List[str] = []

    def emit(self, source: t.Any, message: str) -> None:
        results.append(message)

    monkeypatch.setattr(BaseDisplay, "emit", emit)
    return results


@pytest.fixture
def runner_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with sample config files"""
    (tmp_path / "network.xml").write_bytes(
        b"""<?xml version="1.0" encoding="UTF-8"?>
<Actions>
    <Action name="Foo">
        <command>echo "foo"</command>
        <type>shell</type>
    </Action>
    <Action name="Bar">
        <command>echo "bar"</command>
        <type>shell</type>
        <dependency>Foo</dependency>
    </Action>
</Actions>
"""
    )
    monkeypatch.chdir(tmp_path)
