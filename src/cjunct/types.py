"""
Common types.
"""

import typing as t

from .display.base import BaseDisplay
from .loader.base import AbstractBaseConfigLoader
from .strategy import BaseStrategy

LoaderClassType = t.Type[AbstractBaseConfigLoader]
StrategyClassType = t.Type[BaseStrategy]
DisplayClassType = t.Type[BaseDisplay]

__all__ = [
    "LoaderClassType",
    "StrategyClassType",
    "DisplayClassType",
]
