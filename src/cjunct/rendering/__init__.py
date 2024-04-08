"""All the templating stuff."""

import os
import shlex
import typing as t

from classlogging import LoggerMixin

from . import containers as c
from .tokenizing import TemplarStringLexer
from ..actions.types import RenderedStringTemplate
from ..config.constants import C
from ..exceptions import ActionRenderError

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
            "context": c.ContextDict(context_map),
            "environment": c.LooseDict(os.environ),
        }

    def render(self, value: str) -> RenderedStringTemplate:
        """Process string data, replacing all @{} occurrences"""
        chunks: t.List[str] = []
        for lexeme_type, lexeme_value in TemplarStringLexer(value):
            if lexeme_type == TemplarStringLexer.EXPRESSION:
                lexeme_value = self._string_template_process_expression(expression=lexeme_value)
            chunks.append(lexeme_value)
        return RenderedStringTemplate("".join(chunks))

    @classmethod
    def _string_template_expression_split(cls, string: str) -> t.List[str]:
        """Use shell-style lexer, but split by dots instead of whitespaces"""
        dot_lexer = shlex.shlex(instream=string, punctuation_chars=True)
        dot_lexer.whitespace = "."
        # Extra split to unquote quoted values
        return ["".join(shlex.split(token)) for token in dot_lexer]

    def _string_template_process_expression(self, expression: str) -> str:
        """Split the expression into parts and process according to the part name"""
        self.logger.debug(f"Processing expression: {expression!r}")
        try:
            try:
                # pylint: disable=eval-used
                result: t.Any = eval(
                    expression,
                    {f: None for f in self.DISABLED_GLOBALS},
                    self._locals,
                )
                return str(result)
            except Exception:
                self.logger.debug("Expression evaluation failed", exc_info=True)
                raise
        except ActionRenderError:
            raise
        except (SyntaxError, NameError) as e:
            raise ActionRenderError(e) from e
        except Exception as e:
            raise ActionRenderError(repr(e)) from e

    def _error(self, message: str) -> t.NoReturn:
        self.logger.warning(message)
        raise ActionRenderError(message)
