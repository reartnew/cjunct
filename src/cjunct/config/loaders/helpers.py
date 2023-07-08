"""Common loader utilities"""

import typing as t
from importlib.machinery import ModuleSpec
from importlib.util import (
    spec_from_file_location,
    module_from_spec,
)
from pathlib import Path
from types import ModuleType

from .base import BaseConfigLoader
from .xml import DefaultXMLConfigLoader
from .yaml import DefaultYAMLConfigLoader
from ...exceptions import SourceError

__all__ = [
    "get_default_loader_class_for_file",
    "load_external_module",
]

SUFFIX_TO_LOADER_MAP: t.Dict[str, t.Type[BaseConfigLoader]] = {
    ".xml": DefaultXMLConfigLoader,
    ".yml": DefaultYAMLConfigLoader,
    ".yaml": DefaultYAMLConfigLoader,
}
EXTERNALS_MODULE_NAME: str = "cjunct.external"


def get_default_loader_class_for_file(source: t.Union[str, Path]) -> t.Type[BaseConfigLoader]:
    """Return loader class based on file stats"""
    source_path: Path = Path(source)
    if (loader_class := SUFFIX_TO_LOADER_MAP.get(source_path.suffix)) is None:
        raise SourceError(f"Unrecognized source: {source_path}")
    return loader_class


def load_external_module(source: Path) -> ModuleType:
    """Load an external module"""
    if not source.is_file():
        raise SourceError(f"Missing source module: {source}")
    module_spec: t.Optional[ModuleSpec] = spec_from_file_location(
        name=EXTERNALS_MODULE_NAME,
        location=source,
    )
    if module_spec is None:
        raise SourceError(f"Can't read module spec from source: {source}")
    module: ModuleType = module_from_spec(module_spec)
    module_spec.loader.exec_module(module)  # type: ignore
    return module
