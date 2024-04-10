"""All intercepted errors"""

import typing as t

__all__ = [
    "ExecutionFailed",
    "ActionRenderError",
    "ActionRenderRecursionError",
    "RestrictedBuiltinError",
    "ActionUnionRenderError",
    "ActionRunError",
    "BaseError",
    "LoadError",
    "IntegrityError",
    "SourceError",
    "InteractionError",
]


class ExecutionFailed(Exception):
    """Some steps failed"""


class ActionRenderError(Exception):
    """Action rendering failed"""


class ActionRenderRecursionError(ActionRenderError):
    """Action recursion depth exceeded"""


class RestrictedBuiltinError(Exception):
    """Action rendering access to a restricted builtin function"""


class ActionUnionRenderError(ActionRenderError):
    """Action rendering failed for union field"""


class ActionRunError(Exception):
    """Action execution failed"""


class BaseError(Exception):
    """Common base to catch in CLI"""

    CODE: int = 101


class LoadError(BaseError):
    """Loader regular exception during load process"""

    CODE: int = 102

    def __init__(self, message: str, stack: t.List[str]) -> None:
        self.message: str = message
        self.stack: t.List[str] = stack
        text: str = message
        if stack:
            text += f"\n  Sources stack: {' -> '.join(stack)}"
        super().__init__(text)


class IntegrityError(BaseError):
    """Workflow structure error"""

    CODE: int = 103


class SourceError(BaseError):
    """Source file not recognized"""

    CODE: int = 104


class InteractionError(BaseError):
    """Can't interact with a display"""

    CODE: int = 105
