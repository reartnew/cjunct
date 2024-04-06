"""
Runner has too many dependencies,
thus placed to a separate module.
"""

import io
import os
import re
import shlex
import tokenize
import typing as t

from classlogging import LoggerMixin

from .actions.types import RenderedStringTemplate
from .config.constants import C
from .exceptions import ActionRenderError

__all__ = [
    "Lexer",
    "Templar",
]


class Lexer:
    TEXT: int = 0
    EXPRESSION: int = 1

    def __init__(self, data: str) -> None:
        self._bytes = data.encode()
        self._stream = io.BytesIO(self._bytes)
        self._token_generator = self._ignorant_tokenize()
        self._scanned_lines_length_sum: int = 0
        self._prev_line_length: int = 0
        self._position: int = 0

    def _readline(self):
        line = self._stream.readline()
        self._scanned_lines_length_sum += self._prev_line_length
        self._prev_line_length = len(line)
        return line

    def _get_token(self) -> tokenize.TokenInfo:
        token = next(self._token_generator)
        self._position = self._scanned_lines_length_sum + token.start[1]
        return token

    def _ignorant_tokenize(self) -> t.Generator[tokenize.TokenInfo, None, None]:
        try:
            for token_info in tokenize.tokenize(self._readline):  # type: tokenize.TokenInfo
                yield token_info
        except tokenize.TokenError:
            pass

    def _lex(self):
        armed_at: bool = False
        text_start: int = self._position
        while True:
            try:
                token_info = self._get_token()
                if token_info.type == tokenize.OP and token_info.exact_type == tokenize.AT:
                    armed_at = not armed_at
                if token_info.type == tokenize.OP and token_info.exact_type == tokenize.LBRACE and armed_at:
                    armed_at = False
                    if maybe_text := self._bytes[text_start : self._position - 1]:
                        yield self.TEXT, maybe_text
                    yield self.EXPRESSION, self._read_expression()
                    text_start: int = self._position + 1
            except StopIteration:
                if maybe_text := self._bytes[text_start:]:
                    yield self.TEXT, maybe_text
                break

    def _read_expression(self):
        brace_depth: int = 0
        expr_start: int = self._position + 1
        while True:
            token_info = self._get_token()
            if token_info.type == tokenize.OP and token_info.exact_type == tokenize.LBRACE:
                brace_depth += 1
            elif token_info.type == tokenize.OP and token_info.exact_type == tokenize.RBRACE:
                brace_depth -= 1
            if brace_depth < 0:
                return self._bytes[expr_start : self._position]

    def __iter__(self):
        return self._lex()


class Templar(LoggerMixin):
    """Expression renderer"""

    _LOOSE_OUTCOMES_RENDERING_DEFAULT_VALUE: str = ""
    _TEMPLATE_SUBST_PATTERN: t.Pattern = re.compile(
        r"""
        (?P<prior>
            (?:^|[^@])  # Ensure that match starts from the first @ sign
            (?:@@)*  # Possibly escaped @ signs
        )
        @\{
          (?P<expression>.*?)
        }""",
        re.VERBOSE,
    )

    def __init__(
        self,
        outcomes_getter: t.Callable[[str], t.Optional[t.Dict[str, str]]],
        status_getter: t.Callable[[str], t.Optional[str]],
        raw_context_getter: t.Callable[[str], t.Optional[str]],
    ) -> None:
        self._outcomes_getter = outcomes_getter
        self._status_getter = status_getter
        self._raw_context_getter = raw_context_getter
        self._expression_stack: t.List[str] = []

    def render(self, value: str) -> RenderedStringTemplate:
        """Process string data, replacing all @{} occurrences"""
        replaced_value: str = self._TEMPLATE_SUBST_PATTERN.sub(self._string_template_replace_match, value)
        return RenderedStringTemplate(replaced_value)

    @classmethod
    def _string_template_expression_split(cls, string: str) -> t.List[str]:
        """Use shell-style lexer, but split by dots instead of whitespaces"""
        dot_lexer = shlex.shlex(instream=string, punctuation_chars=True)
        dot_lexer.whitespace = "."
        # Extra split to unquote quoted values
        return ["".join(shlex.split(token)) for token in dot_lexer]

    def _string_template_replace_match(self, match: t.Match) -> str:
        """Helper function for template substitution using re.sub"""
        prior: str = match.groupdict()["prior"]
        expression: str = match.groupdict()["expression"]
        expression_substitution_result: str = self._string_template_process_expression(expression)
        return f"{prior}{expression_substitution_result}"

    def _string_template_process_expression(self, expression: str) -> str:
        """Split the expression into parts and process according to the part name"""
        self.logger.debug(f"Processing expression: {expression!r}")
        if expression in self._expression_stack:
            self._error(f"Expression cycle: {' -> '.join(self._expression_stack + [expression])}")
        self._expression_stack.append(expression)
        try:
            all_parts: t.List[str] = self._string_template_expression_split(expression)
            part_type, *other_parts = all_parts
            if part_type == "outcomes":
                if len(all_parts) != 3:
                    self._error(f"Outcomes expression has {len(all_parts)} parts of 3")
                action_name, key = other_parts
                actions_outcomes: t.Optional[t.Dict[str, str]] = self._outcomes_getter(action_name)
                if actions_outcomes is None:
                    self._error(f"Action not found: {action_name!r}")
                outcome: t.Optional[str] = actions_outcomes.get(key)
                if outcome is None:
                    if C.STRICT_OUTCOMES_RENDERING:
                        self._error(f"Action {action_name!r} outcome key {key!r} not found")
                    else:
                        outcome = self._LOOSE_OUTCOMES_RENDERING_DEFAULT_VALUE
                return outcome
            if part_type == "status":
                if len(all_parts) != 2:
                    self._error(f"Status expression has {len(all_parts)} parts of 2")
                (action_name,) = other_parts
                if (action_status := self._status_getter(action_name)) is None:
                    self._error(f"Action not found: {action_name!r}")
                return action_status
            if part_type == "environment":
                if len(all_parts) != 2:
                    self._error(f"Environment expression has {len(all_parts)} parts of 2")
                (variable_name,) = other_parts
                return os.getenv(variable_name, "")
            if part_type == "context":
                if len(all_parts) != 2:
                    self._error(f"Context expression has {len(all_parts)} parts of 2")
                (context_key,) = other_parts
                if (raw_context_value := self._raw_context_getter(context_key)) is None:
                    self._error(f"Context key not found: {context_key!r}")
                return self.render(raw_context_value)
            self._error(f"Unknown expression type: {part_type!r}")
        finally:
            self._expression_stack.pop()

    def _error(self, message: str) -> t.NoReturn:
        if self._expression_stack:
            message = f"{message} (from {self._expression_stack[0]!r})"
        self.logger.warning(message)
        raise ActionRenderError(message)
