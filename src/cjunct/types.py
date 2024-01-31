"""
Common types.
"""

import typing as t

from .config.loaders.base import AbstractBaseConfigLoader
from .display.base import BaseDisplay
from .strategy import BaseStrategy

LoaderClassType = t.Type[AbstractBaseConfigLoader]
StrategyClassType = t.Type[BaseStrategy]
DisplayClassType = t.Type[BaseDisplay]

__all__ = [
    "LoaderClassType",
    "StrategyClassType",
    "DisplayClassType",
]
