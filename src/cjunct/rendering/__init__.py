"""All the templating stuff."""

import shlex
import typing as t

from classlogging import LoggerMixin

from .tokenizing import TemplarStringLexer
from ..actions.types import RenderedStringTemplate
from ..exceptions import ActionRenderError

__all__ = [
    "Templar",
]


class Templar(LoggerMixin):
    """Expression renderer"""

    DISABLED_GLOBALS: t.List[str] = ["exec", "eval", "compile", "setattr", "delattr"]

    def __init__(self, **kwargs) -> None:
        self._locals = kwargs

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
