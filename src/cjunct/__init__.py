"""Declarative parallel process runner"""

from .version import __version__
from .runner import Runner
from .strategy import (
    FreeStrategy,
    SequentialStrategy,
    LooseStrategy,
)
