"""All non-intercepted errors"""

import typing as t

__all__ = [
    "BaseError",
    "LoadError",
    "IntegrityError",
    "SourceError",
]


class BaseError(Exception):
    """Common base to catch in CLI"""

    CODE: int = 1


class LoadError(BaseError):
    """Loader regular exception during load process"""

    CODE: int = 2

    def __init__(self, message: str, stack: t.List[str]) -> None:
        self.message: str = message
        self.stack: t.List[str] = stack
        text: str = message
        if stack:
            text += f"\nCurrent stack: {' -> '.join(stack)}"
        super().__init__(text)


class IntegrityError(BaseError):
    """Action net structure error"""

    CODE: int = 3


class SourceError(BaseError):
    """Source file not recognized"""

    CODE: int = 4
