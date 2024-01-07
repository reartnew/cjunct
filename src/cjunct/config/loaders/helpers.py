"""Common loader utilities"""

import typing as t
from pathlib import Path

from .base import AbstractBaseConfigLoader
from .default.xml import DefaultXMLConfigLoader
from .default.yaml import DefaultYAMLConfigLoader
from ...exceptions import SourceError

__all__ = [
    "get_default_loader_class_for_file",
]

SUFFIX_TO_LOADER_MAP: t.Dict[str, t.Type[AbstractBaseConfigLoader]] = {
    ".xml": DefaultXMLConfigLoader,
    ".yml": DefaultYAMLConfigLoader,
    ".yaml": DefaultYAMLConfigLoader,
}


def get_default_loader_class_for_file(source: t.Union[str, Path]) -> t.Type[AbstractBaseConfigLoader]:
    """Return loader class based on file stats"""
    source_path: Path = Path(source)
    if (loader_class := SUFFIX_TO_LOADER_MAP.get(source_path.suffix)) is None:
        raise SourceError(f"Unrecognized source: {source_path}")
    return loader_class
