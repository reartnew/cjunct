# pylint: disable=missing-function-docstring,unused-argument

import sys
from pathlib import Path

import classlogging
import pytest


def pytest_sessionstart(session):
    tests_dir: Path = Path(__file__).parent
    assert tests_dir.name == "tests"  # Just to be sure
    source_dir: Path = tests_dir.parent / "src"
    sys.path.append(str(source_dir))


@pytest.fixture(autouse=True, scope="session")
def configure_logging() -> None:
    classlogging.configure_logging(level=classlogging.LogLevel.DEBUG)
