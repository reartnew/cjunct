"""Runner call fixtures"""
# pylint: disable=unused-argument

import contextlib
import os
import typing as t
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from cjunct import exceptions
from cjunct.actions import Action
from cjunct.display import BaseDisplay


@contextlib.contextmanager
def pushd(target: Path) -> t.Generator[None, None, None]:
    """Working directory change helper"""
    known_dir: Path = Path.cwd()
    os.chdir(target)
    try:
        yield
    finally:
        os.chdir(known_dir)


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
    with pushd(tmp_path):
        yield


@pytest.fixture(
    params=[
        "external-deps-additionals",
        "external-deps-bootstrap-skip-through",
        "external-deps-core",
        "simple-with-checklists",
        "simple-with-deps-and-dummies",
        "simple-with-deps",
        "simple-with-external-deps",
        "simple",
    ],
)
def good_xml_config(request: SubRequest, project_root: Path) -> t.Generator[Path, None, None]:
    """Return sample config file path"""
    configs_dir: Path = project_root / "tests" / "runner" / "samples" / "config" / "xml" / "synthetic" / "good"
    with pushd(configs_dir):
        yield configs_dir / f"{request.param}.xml"


@pytest.fixture(
    params=[
        ("plain-checklist-collision", exceptions.LoadError, "Checklist defined twice"),
        ("plain-checklist-reserved-name", exceptions.LoadError, "Reserved checklist name used"),
        ("plain-double-declaration", exceptions.LoadError, "Action declared twice"),
        ("plain-missing-checklists-source", exceptions.LoadError, "No such directory"),
        ("plain-missing-deps", exceptions.IntegrityError, "Missing actions among dependencies"),
    ],
)
def bad_xml_config(
    request: SubRequest, project_root: Path
) -> t.Generator[t.Tuple[Path, t.Type[Exception], str], None, None]:
    """Return sample config file path with error to handle"""
    configs_dir: Path = project_root / "tests" / "runner" / "samples" / "config" / "xml" / "synthetic" / "bad"
    config_name, exception, match = request.param
    with pushd(configs_dir):
        yield configs_dir / f"{config_name}.xml", exception, match
