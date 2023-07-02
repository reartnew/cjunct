"""Lazy-loaded constants"""

from pathlib import Path

from .helpers import (
    Optional,
    Mandatory,
    maybe_path,
)
from ..environment import Env

__all__ = [
    "C",
]


class C:
    """Runtime constants"""

    CONTEXT_DIRECTORY: Mandatory[Path] = Mandatory(
        lambda: maybe_path(Env.CJUNCT_CONTEXT_DIRECTORY),
        lambda: Path().resolve(),
    )
    ACTIONS_SOURCE_FILE: Optional[Path] = Optional(
        lambda: maybe_path(Env.CJUNCT_ACTIONS_SOURCE_FILE),
    )
