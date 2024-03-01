"""The package describes actions and their mutual relations"""

from .base import (
    ActionBase,
    ActionDependency,
    ActionStatus,
    ActionSkip,
    Stderr,
    ArgsBase,
)
from .net import ActionNet
