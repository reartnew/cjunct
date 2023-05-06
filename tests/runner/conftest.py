# pylint: disable=unused-argument
import os
import typing as t
from pathlib import Path

import pytest

from cjunct.actions import Action
from cjunct.display import BaseDisplay


@pytest.fixture(autouse=True, scope="session")
def action_echo_mock():
    """Add action extra behaviours.
    Normally it should be done via Action subclassing and loader change,
    but who cares: it's just a test"""

    async def echo(self) -> t.AsyncGenerator[str, None]:
        yield self.command

    # pylint: disable=protected-access
    Action._TYPE_HANDLERS["test-echo"] = echo


@pytest.fixture
def display_collector(monkeypatch) -> t.List[str]:
    """Creates display events list instead of putting them to stdout"""
    results: t.List[str] = []

    def emit(self, source: t.Any, message: str) -> None:
        results.append(message)

    monkeypatch.setattr(BaseDisplay, "emit", emit)
    return results


@pytest.fixture
def runner_context(tmp_path: Path) -> t.Generator:
    """Prepare a directory with sample config files"""
    known_dir: str = os.getcwd()
    (tmp_path / "network.xml").write_bytes(
        b"""<Actions>
    <Action name="Foo">
        <command>echoing "foo"</command>
        <type>test-echo</type>
    </Action>
    <Action name="Bar">
        <command>echoing "bar"</command>
        <type>test-echo</type>
        <dependency>Foo</dependency>
    </Action>
</Actions>
"""
    )
    os.chdir(tmp_path)
    yield
    os.chdir(known_dir)
