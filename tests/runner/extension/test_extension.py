"""Check extension possibilities"""
# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest

import cjunct
from cjunct.exceptions import SourceError

MODULES_DIR: Path = Path(__file__).parent / "modules"


def test_good_ext_loader(echo_context: None, monkeypatch: pytest.MonkeyPatch, display_collector: t.List[str]) -> None:
    """Validate external loader"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "good_loader.py"))
    cjunct.Runner().run_sync()
    assert display_collector == [
        "[Foo] | foo",
        "============",
        "SUCCESS: Foo",
    ]


def test_ext_loader_missing_attr(echo_context: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check incomplete module"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "bad_loader.py"))
    with pytest.raises(AttributeError, match="External module contains no class 'ConfigLoader'"):
        cjunct.Runner().run_sync()


def test_ext_loader_invalid_source(echo_context: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check non-module"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "non_loader.txt"))
    with pytest.raises(SourceError, match="Can't read module spec from source"):
        cjunct.Runner().run_sync()


def test_ext_loader_missing_source(echo_context: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check missing module"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "missing_loader.py"))
    with pytest.raises(SourceError, match="Missing source module"):
        cjunct.Runner().run_sync()
