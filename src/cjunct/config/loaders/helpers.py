import typing as t
from pathlib import Path

from .base import BaseConfigLoader
from .exceptions import SourceError
from .xml import XMLConfigLoader

__all__ = [
    "get_default_loader_for_file",
]


def get_default_loader_for_file(source: t.Union[str, Path]) -> BaseConfigLoader:
    """Return loader based on file stats"""
    source_path: Path = Path(source)
    if source_path.suffix == ".xml":
        return XMLConfigLoader()
    raise SourceError(f"Unrecognized source: {source_path}")
