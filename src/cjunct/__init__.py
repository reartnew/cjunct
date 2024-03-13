"""Declarative parallel process runner"""

from .config.constants import C
from .runner import Runner
from .strategy import (
    FreeStrategy,
    SequentialStrategy,
    LooseStrategy,
)
from .actions.base import (
    ActionBase,
    ArgsBase,
    Stderr,
    StringTemplate,
)

from .version import __version__
