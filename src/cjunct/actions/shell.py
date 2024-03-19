"""Backwards-compatibility shim. Will be removed in next major version."""

from .bundled.shell import ShellAction, ShellArgs

__all__ = [
    "ShellAction",
    "ShellArgs",
]
