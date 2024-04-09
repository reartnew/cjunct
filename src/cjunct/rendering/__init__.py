"""All the templating stuff."""

import os
import typing as t

from classlogging import LoggerMixin

from . import containers as c
from .tokenizing import TemplarStringLexer
from ..actions.types import RenderedStringTemplate
from ..config.constants import C
from ..exceptions import ActionRenderError, RestrictedBuiltinError, ActionRenderRecursionError

__all__ = [
    "Templar",
]


class Templar(LoggerMixin):
    """Expression renderer"""

    DISABLED_GLOBALS: t.List[str] = ["exec", "eval", "compile", "setattr", "delattr"]

    def __init__(
        self,
        outcomes_map: t.Mapping[str, t.Mapping[str, str]],
        action_states: t.Mapping[str, str],
        context_map: t.Mapping[str, str],
    ) -> None:
        outcomes_leaf_class: t.Type[dict] = (
            c.StrictOutcomeDict if C.STRICT_OUTCOMES_RENDERING else c.LooseDict  # type: ignore
        )
        self._locals: t.Dict[str, t.Any] = {
            "outcomes": c.ActionContainingDict(
                {name: outcomes_leaf_class(outcomes_map.get(name, {})) for name in action_states}
            ),
            "status": c.ActionContainingDict(action_states),
            "context": c.ContextDict(data=context_map, render_hook=self._internal_render),
            "environment": c.LooseDict(os.environ),
        }

    def render(self, value: str) -> RenderedStringTemplate:
        """Process string data, replacing all @{} occurrences."""
        try:
            return self._internal_render(value)
        except ActionRenderRecursionError as e:
            # Eliminate ActionRenderRecursionError stack trace on hit
            self.logger.debug(f"Rendering {value!r} failed: {e!r}")
            raise ActionRenderError(e) from None
        except ActionRenderError as e:
            self.logger.debug(f"Rendering {value!r} failed: {e!r}", exc_info=True)
            raise

    def _internal_render(self, value: str) -> RenderedStringTemplate:
        """Recursive rendering routine"""
        chunks: t.List[str] = []
        # Cheap check
        if "@{" not in value:
            return RenderedStringTemplate(value)
        for lexeme_type, lexeme_value in TemplarStringLexer(value):
            if lexeme_type == TemplarStringLexer.EXPRESSION:
                lexeme_value = self._string_template_process_expression(expression=lexeme_value)
            chunks.append(lexeme_value)
        return RenderedStringTemplate("".join(chunks))

    @classmethod
    def _make_restricted_builtin_call_shim(cls, name: str) -> t.Callable:
        def _call(*args, **kwargs) -> t.NoReturn:
            raise RestrictedBuiltinError(name)

        return _call

    def _string_template_process_expression(self, expression: str) -> str:
        """Split the expression into parts and process according to the part name"""
        self.logger.debug(f"Processing expression: {expression!r}")
        try:
            # pylint: disable=eval-used
            result: t.Any = eval(  # nosec
                expression,
                {f: self._make_restricted_builtin_call_shim(f) for f in self.DISABLED_GLOBALS},
                self._locals,
            )
            return str(result)
        except ActionRenderError:
            raise
        except (SyntaxError, NameError) as e:
            self.logger.warning(repr(e))
            raise ActionRenderError(e) from e
        except Exception as e:
            self.logger.warning(repr(e))
            raise ActionRenderError(repr(e)) from e
