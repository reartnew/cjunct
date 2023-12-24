"""Lazy-loaded constants helpers"""

import types
import typing as t
from pathlib import Path

from ..loaders.helpers import load_external_module
from ...strategy import KNOWN_STRATEGIES
from ...types import StrategyClassType

__all__ = [
    "Optional",
    "Mandatory",
    "maybe_path",
    "maybe_class_from_module",
    "maybe_strategy",
]

VT = t.TypeVar("VT")
GetterType = t.Callable[[], t.Optional[VT]]


class Optional(t.Generic[VT]):
    """Optional lazy variable"""

    def __init__(self, *getters: GetterType) -> None:
        self._getters: t.Tuple[GetterType, ...] = getters
        self._name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def __get__(self, instance: t.Any, owner: type) -> t.Optional[VT]:
        getter_result: t.Optional[VT] = None
        for getter in self._getters:
            if (getter_result := getter()) is not None:
                break
        return getter_result


class Mandatory(Optional, t.Generic[VT]):
    """Mandatory lazy variable"""

    def __get__(self, instance: t.Any, owner: type) -> VT:
        result: t.Optional[VT] = super().__get__(instance, owner)
        if result is None:
            raise ValueError(f"{self._name!r} getters failed")
        return result


def maybe_path(path_str: str) -> t.Optional[Path]:
    """Transform a string into an optional path"""
    return Path(path_str) if path_str else None


def maybe_strategy(name: t.Optional[str]) -> t.Optional[StrategyClassType]:
    """Transform an optional strategy name into an optional strategy class"""
    return KNOWN_STRATEGIES[name] if name else None


def maybe_class_from_module(path_str: str, class_name: str) -> t.Optional[type]:
    """Get a class from an external module, if given"""
    if (source_path := maybe_path(path_str)) is None:
        return None
    module: types.ModuleType = load_external_module(source_path)
    if not hasattr(module, class_name):
        raise AttributeError(f"External module contains no class {class_name!r} in {path_str!r}")
    return getattr(module, class_name)
