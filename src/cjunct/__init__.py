"""Declarative parallel process runner"""

from .config.constants import C
from .runner import Runner
from .strategy import (
    FreeStrategy,
    SequentialStrategy,
    LooseStrategy,
)
from .version import __version__
