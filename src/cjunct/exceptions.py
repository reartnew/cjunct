"""All non-intercepted errors"""

import typing as t

__all__ = [
    "LoadError",
    "IntegrityError",
    "SourceError",
    "ActionStructureError",
]


class LoadError(Exception):
    """Loader regular exception during load process"""

    def __init__(self, message: str, stack: t.List[str]) -> None:
        self.message: str = message
        self.stack: t.List[str] = stack
        text: str = message
        if stack:
            text += f"\nCurrent stack: {' -> '.join(stack)}"
        super().__init__(text)


class IntegrityError(Exception):
    """Action net structure error"""


class SourceError(Exception):
    """Source file not recognized"""


class ActionStructureError(Exception):
    """Certain action structure mismatch"""
