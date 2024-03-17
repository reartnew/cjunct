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
)
from .actions.types import (
    Stderr,
    StringTemplate,
)

from .version import __version__
