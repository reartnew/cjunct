"""Loader call fixtures"""
# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from cjunct import exceptions


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
def good_xml_config_path(
    request: SubRequest,
    project_root: Path,
    pushd: t.Callable,
) -> t.Generator[Path, None, None]:
    """Return sample config file path"""
    configs_dir: Path = project_root / "tests" / "config" / "loaders" / "samples" / "config" / "xml" / "good"
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
    request: SubRequest,
    project_root: Path,
    pushd: t.Callable,
) -> t.Generator[t.Tuple[Path, t.Type[Exception], str], None, None]:
    """Return sample config file path with error to handle"""
    configs_dir: Path = project_root / "tests" / "config" / "loaders" / "samples" / "config" / "xml" / "bad"
    config_name, exception, match = request.param
    with pushd(configs_dir):
        yield configs_dir / f"{config_name}.xml", exception, match
