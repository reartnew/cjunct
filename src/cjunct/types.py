"""
Common types.
"""

import typing as t

from .display.base import BaseDisplay
from .loader.base import AbstractBaseWorkflowLoader
from .strategy import BaseStrategy

LoaderClassType = t.Type[AbstractBaseWorkflowLoader]
StrategyClassType = t.Type[BaseStrategy]
DisplayClassType = t.Type[BaseDisplay]
LoaderType: t.TypeAlias = AbstractBaseWorkflowLoader
StrategyType: t.TypeAlias = BaseStrategy
DisplayType: t.TypeAlias = BaseDisplay

__all__ = [
    "LoaderClassType",
    "StrategyClassType",
    "DisplayClassType",
    "LoaderType",
    "StrategyType",
    "DisplayType",
]
