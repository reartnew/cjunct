import typing as t
from pathlib import Path

from .base import BaseConfigLoader
from .xml import XMLConfigLoader
from ...exceptions import SourceError

__all__ = [
    "get_default_loader_class_for_file",
]


def get_default_loader_class_for_file(source: t.Union[str, Path]) -> t.Type[BaseConfigLoader]:
    """Return loader class based on file stats"""
    source_path: Path = Path(source)
    if source_path.suffix == ".xml":
        return XMLConfigLoader
    raise SourceError(f"Unrecognized source: {source_path}")
