"""Runner call fixtures"""

import typing as t
from pathlib import Path

import pytest

from cjunct.display import BaseDisplay


@pytest.fixture
def display_collector(monkeypatch: pytest.MonkeyPatch) -> t.List[str]:
    """Creates display events list instead of putting them to stdout"""
    results: t.List[str] = []

    # pylint: disable=unused-argument
    def display(self, message: str) -> None:
        results.append(message)

    monkeypatch.setattr(BaseDisplay, "display", display)
    return results


@pytest.fixture
def runner_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare a directory with sample config files"""
    (tmp_path / "network.xml").write_bytes(
        b"""<?xml version="1.0" encoding="UTF-8"?>
<Actions>
    <Action name="Foo">
        <command>echo &quot;foo&quot;</command>
        <type>shell</type>
    </Action>
    <Action name="Bar">
        <command>echo &quot;bar&quot; &gt;&amp;2</command>
        <type>shell</type>
        <dependency>Foo</dependency>
    </Action>
</Actions>
"""
    )
    monkeypatch.chdir(tmp_path)
