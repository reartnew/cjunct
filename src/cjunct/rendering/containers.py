"""Templar containers for rendering."""

import typing as t

from .constants import MAX_RECURSION_DEPTH
from ..actions.types import RenderedStringTemplate
from ..exceptions import ActionRenderError, ActionRenderRecursionError

__all__ = [
    "LooseDict",
    "StrictOutcomeDict",
    "ActionContainingDict",
    "ContextDict",
]


class AttrDict(dict):
    """A dictionary that allows attribute read access to its keys"""

    def __getattr__(self, item: str):
        return self[item]

    def __getitem__(self, item: str):
        try:
            return super().__getitem__(item)
        except KeyError as e:
            return self._on_key_error(e)

    @classmethod
    def _on_key_error(cls, e: KeyError) -> t.Any:
        raise NotImplementedError


class LooseDict(AttrDict):
    """A dictionary that allows attribute read access to its keys with a default empty value fallback"""

    @classmethod
    def _on_key_error(cls, e: KeyError) -> t.Any:
        return ""


class StrictOutcomeDict(AttrDict):
    """A dictionary that allows attribute read access to its keys with a default value fallback"""

    @classmethod
    def _on_key_error(cls, e: KeyError) -> t.Any:
        raise ActionRenderError(f"Outcome key {e} not found") from e


class ActionContainingDict(AttrDict):
    """Anything with action names as keys"""

    @classmethod
    def _on_key_error(cls, e: KeyError) -> t.Any:
        raise ActionRenderError(f"Action not found: {e}") from e


class ContextDict(AttrDict):
    """Context keys representation"""

    def __init__(self, data: t.Mapping[str, str], render_hook: t.Callable[[str], RenderedStringTemplate]) -> None:
        super().__init__(data)
        self.__render_hook: t.Callable[[str], RenderedStringTemplate] = render_hook
        self.__depth: int = 0

    @classmethod
    def _on_key_error(cls, e: KeyError) -> t.Any:
        raise ActionRenderError(f"Context key not found: {e}") from e

    def __getitem__(self, item: str):
        # Context keys can refer to anything else, thus we keep resolving until the template is stable
        result = super().__getitem__(item)
        while True:
            # Only strings should be rendered further
            if not isinstance(result, str):
                break
            self.__depth += 1
            if self.__depth >= MAX_RECURSION_DEPTH:
                # This exception floats to the very "render" call without any logging
                raise ActionRenderRecursionError(f"Recursion depth exceeded: {self.__depth}/{MAX_RECURSION_DEPTH}")
            try:
                if result == (result := self.__render_hook(result)):
                    break
            finally:
                self.__depth -= 1
        return result
