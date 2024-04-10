"""Templar containers for rendering."""

import typing as t

from ..actions.types import RenderedStringTemplate
from ..exceptions import ActionRenderError

__all__ = [
    "AttrDict",
    "LooseDict",
    "StrictOutcomeDict",
    "ActionContainingDict",
    "ContextDict",
    "DeferredStringTemplate",
]

RenderHookType = t.Callable[[str], RenderedStringTemplate]


class ItemAttributeAccessorMixin:
    """Anything, that can be accessed fie __getitem__, is available also as an attribute"""

    def __getattr__(self, item: str):
        return self.__getitem__(item)


class AttrDict(dict, ItemAttributeAccessorMixin):
    """Basic dictionary that allows attribute read access to its keys"""


class LooseDict(AttrDict):
    """A dictionary that allows attribute read access to its keys with a default empty value fallback"""

    def __getitem__(self, item: str):
        try:
            return super().__getitem__(item)
        except KeyError:
            return ""


class StrictOutcomeDict(AttrDict):
    """A dictionary that allows attribute read access to its keys with a default value fallback"""

    def __getitem__(self, item: str):
        try:
            return super().__getitem__(item)
        except KeyError as e:
            raise ActionRenderError(f"Outcome key {e} not found") from e


class ActionContainingDict(AttrDict):
    """Anything with action names as keys"""

    def __getitem__(self, item: str):
        try:
            return super().__getitem__(item)
        except KeyError as e:
            raise ActionRenderError(f"Action not found: {e}") from e


class ContextDict(AttrDict):
    """Context keys representation"""

    def __getitem__(self, item: str):
        # Context keys can refer to anything else, thus we keep resolving until the template is stable
        try:
            return super().__getitem__(item)
        except KeyError as e:
            raise ActionRenderError(f"Context key not found: {e}") from e


class DeferredStringTemplate:
    """An object that triggers self-rendering when being cast into a string"""

    def __init__(self, text: str, render_hook: RenderHookType) -> None:
        self.__text = text
        self.__render_hook: RenderHookType = render_hook

    def __str__(self) -> str:
        return self.__render_hook(self.__text)

    def __repr__(self) -> str:
        return repr(str(self))
