"""Bind """

from ..base import AbstractBaseConfigLoader
from ....actions.shell import ShellAction

__all__ = [
    "DefaultRootConfigLoader",
]


# pylint: disable=abstract-method
class DefaultRootConfigLoader(AbstractBaseConfigLoader):
    """Bind default actions to abstract base"""

    ACTION_FACTORIES = {"shell": ShellAction}
