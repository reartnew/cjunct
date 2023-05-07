"""Loader call fixtures"""
# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from cjunct import exceptions

BadConfigType = t.Tuple[str, t.Type[Exception], str]

_GOOD_CONFIGS_NAMES: t.List[str] = [
    "external-deps-additionals",
    "external-deps-bootstrap-skip-through",
    "external-deps-core",
    "simple-with-checklists",
    "simple-with-deps-and-dummies",
    "simple-with-deps",
    "simple-with-external-deps",
    "simple",
]

_BAD_CONFIGS_NAMES: t.List[BadConfigType] = [
    ("plain-checklist-collision", exceptions.LoadError, "Checklist defined twice"),
    ("plain-checklist-reserved-name", exceptions.LoadError, "Reserved checklist name used"),
    ("plain-double-declaration", exceptions.LoadError, "Action declared twice"),
    ("plain-missing-checklists-source", exceptions.LoadError, "No such directory"),
    ("plain-missing-deps", exceptions.IntegrityError, "Missing actions among dependencies"),
]


@pytest.fixture(params=_GOOD_CONFIGS_NAMES)
def good_xml_config_path(
    request: SubRequest,
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Return sample config file path"""
    configs_dir: Path = project_root / "tests" / "config" / "loaders" / "samples" / "xml" / "good"
    monkeypatch.chdir(configs_dir)
    return configs_dir / f"{request.param}.xml"


@pytest.fixture(params=_BAD_CONFIGS_NAMES, ids=[cfg[0] for cfg in _BAD_CONFIGS_NAMES])
def bad_xml_config(
    request: SubRequest,
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> t.Tuple[Path, t.Type[Exception], str]:
    """Return sample config file path with error to handle"""
    configs_dir: Path = project_root / "tests" / "config" / "loaders" / "samples" / "xml" / "bad"
    config_name, exception, match = request.param
    monkeypatch.chdir(configs_dir)
    return configs_dir / f"{config_name}.xml", exception, match
