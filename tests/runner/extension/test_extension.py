"""Check extension possibilities"""

# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest

import cjunct
from cjunct.exceptions import SourceError, LoadError, ExecutionFailed

MODULES_DIR: Path = Path(__file__).parent / "modules"


def test_good_ext_loader(echo_context: None, monkeypatch: pytest.MonkeyPatch, display_collector: t.List[str]) -> None:
    """Validate external loader"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "good_loader.py"))
    monkeypatch.setenv("CJUNCT_EXTERNAL_MODULES_PATHS", str(MODULES_DIR))
    cjunct.Runner().run_sync()
    assert display_collector == [
        "[Foo]  | foo",
        "============",
        "SUCCESS: Foo",
    ]


def test_ext_loader_missing_attr(echo_context: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check incomplete module"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "empty_loader.py"))
    with pytest.raises(AttributeError, match="External module contains no class 'ConfigLoader'"):
        cjunct.Runner().run_sync()


def test_ext_loader_bad_no_args_action(echo_context: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check module with bad actions without args"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "bad_no_args_actions_loader.py"))
    with pytest.raises(LoadError, match="Couldn't find an `args` annotation for class"):
        cjunct.Runner().run_sync()


def test_ext_loader_bad_arg_name_action(echo_context: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check module with bad actions with reserved args"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "bad_arg_name_actions_loader.py"))
    with pytest.raises(TypeError, match="Reserved names found in 'ReservedArgs' class definition"):
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


def test_ext_loader_return_string(
    string_returning_context: None,
    monkeypatch: pytest.MonkeyPatch,
    display_collector: t.List[str],
) -> None:
    """Check exotic returns from actions"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "good_loader.py"))
    monkeypatch.setenv("CJUNCT_EXTERNAL_MODULES_PATHS", str(MODULES_DIR))
    cjunct.Runner().run_sync()
    assert display_collector == [
        "============",
        "SUCCESS: Foo",
    ]


def test_imports_context_isolation(
    context_keys_isolation_context: None,
    monkeypatch: pytest.MonkeyPatch,
    display_collector: t.List[str],
) -> None:
    """Check that 'context' fields are not being imported"""
    monkeypatch.setenv("CJUNCT_CONFIG_LOADER_SOURCE_FILE", str(MODULES_DIR / "good_loader.py"))
    monkeypatch.setenv("CJUNCT_EXTERNAL_MODULES_PATHS", str(MODULES_DIR))
    with pytest.raises(ExecutionFailed):
        cjunct.Runner().run_sync()
    assert (
        "[Foo] !| Action 'Foo' rendering failed: Context key not found: 'imported-key' (from 'context.imported-key')"
        in display_collector
    )
