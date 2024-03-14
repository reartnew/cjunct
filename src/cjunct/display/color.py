"""Colorizing utils"""

from ..config.constants import C

__all__ = [
    "Color",
]


class Color:
    """Text color wrapping"""

    @classmethod
    def gray(cls, message: str) -> str:
        """Make a string gray"""
        return cls._add_formatting(message, 90)

    @classmethod
    def red(cls, message: str) -> str:
        """Make a string red"""
        return cls._add_formatting(message, 31)

    @classmethod
    def green(cls, message: str) -> str:
        """Make a string green"""
        return cls._add_formatting(message, 32)

    @classmethod
    def yellow(cls, message: str) -> str:
        """Make a string green"""
        return cls._add_formatting(message, 33)

    @classmethod
    def _add_formatting(cls, message: str, code: int) -> str:
        return message if not C.USE_COLOR else f"\u001b[{code}m{message}\u001b[0m"
