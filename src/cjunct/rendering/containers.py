"""Templar containers for rendering."""

import typing as t

from ..exceptions import ActionRenderError

__all__ = [
    "AttrDict",
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
        raise e


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

    @classmethod
    def _on_key_error(cls, e: KeyError) -> t.Any:
        raise ActionRenderError(f"Context key not found: {e}") from e
