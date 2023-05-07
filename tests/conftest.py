"""Session-wide fixtures"""
# pylint: disable=missing-function-docstring,unused-argument

import contextlib
import os
import sys
import typing as t
from pathlib import Path

import classlogging
import pytest

_PROJECT_ROOT: Path = Path(__file__).parents[1]


def pytest_sessionstart(session):
    source_dir: Path = _PROJECT_ROOT / "src"
    assert source_dir.is_dir()
    sys.path.append(str(source_dir))


@pytest.fixture(scope="session")
def project_root() -> Path:
    return _PROJECT_ROOT


@pytest.fixture(autouse=True, scope="session")
def configure_logging() -> None:
    classlogging.configure_logging(level=classlogging.LogLevel.DEBUG)


@pytest.fixture(scope="session")
def pushd() -> t.Callable:
    """Working directory change helper"""

    @contextlib.contextmanager
    def _pushd(target: Path) -> t.Generator[None, None, None]:
        known_dir: Path = Path.cwd()
        os.chdir(target)
        try:
            yield
        finally:
            os.chdir(known_dir)

    return _pushd
