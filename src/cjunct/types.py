"""
Common types.
"""

import typing as t

from .config.loaders.base import BaseConfigLoader
from .display.base import BaseDisplay
from .strategy import BaseStrategy

LoaderClassType = t.Type[BaseConfigLoader]
StrategyClassType = t.Type[BaseStrategy]
DisplayClassType = t.Type[BaseDisplay]

__all__ = [
    "LoaderClassType",
    "StrategyClassType",
    "DisplayClassType",
]
