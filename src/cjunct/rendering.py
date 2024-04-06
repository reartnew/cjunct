"""All the templating stuff."""

import io
import os
import shlex
import tokenize
import typing as t

from classlogging import LoggerMixin

from .actions.types import RenderedStringTemplate
from .config.constants import C
from .exceptions import ActionRenderError

__all__ = [
    "ExpressionTokenizer",
    "TemplarStringLexer",
    "Templar",
]


class ExpressionTokenizer:
    """Utilize tokenize.tokenize while simultaneously tracking the caret position"""

    def __init__(self, data: str) -> None:
        self._bytes: bytes = data.encode()
        self._stream: io.BytesIO = io.BytesIO(self._bytes)
        self._token_generator: t.Iterator[tokenize.TokenInfo] = self._careless_tokenize()
        self._scanned_lines_length_sum: int = 0
        self._prev_line_length: int = 0
        self.position: int = 0

    def _readline(self) -> bytes:
        """Memorize read lines length sum"""
        line: bytes = self._stream.readline()
        self._scanned_lines_length_sum += self._prev_line_length
        self._prev_line_length = len(line)
        return line

    def _careless_tokenize(self) -> t.Generator[tokenize.TokenInfo, None, None]:
        """Tokenize the stream, while ignoring all `TokenError`s"""
        try:
            yield from tokenize.tokenize(self._readline)
        except tokenize.TokenError:
            pass

    def get_token(self) -> tokenize.TokenInfo:
        """Yield a token and memorize its original position"""
        token: tokenize.TokenInfo = next(self._token_generator)
        self.position = self._scanned_lines_length_sum + token.start[1]
        return token

    def __iter__(self) -> t.Iterator[tokenize.TokenInfo]:
        return self

    def __next__(self) -> tokenize.TokenInfo:
        return self.get_token()


class TemplarStringLexer:
    """Emit raw text and expressions separately"""

    TEXT: int = 0
    EXPRESSION: int = 1
    _IGNORED_TOKENS_TYPES = [
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.ENCODING,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
    ]

    def __init__(self, data: str) -> None:
        self._data: str = data
        self._len: int = len(data)
        self._caret: int = 0

    def _get_symbol(self) -> str:
        """Read the next symbol of the input data"""
        if self._caret >= self._len:
            raise EOFError
        self._caret += 1
        return self._data[self._caret - 1]

    def __iter__(self) -> t.Iterator[t.Tuple[int, str]]:
        """Alternately yield raw text to leave as is and expressions to evaluate"""
        armed_at: bool = False
        text_start: int = self._caret
        while True:
            try:
                # Each expression starts with an "@{" pair, which can be escaped by doubling the "@" down,
                # thus each second "@" disengages the expression scanning readiness
                if (symbol := self._get_symbol()) == "@":
                    armed_at = not armed_at
                    continue
                if symbol == "{" and armed_at:
                    if maybe_text := self._data[text_start : self._caret - 2]:  # -2 stands for the "@{"
                        yield self.TEXT, maybe_text
                    expression_source_length, expression = self._read_expression()
                    yield self.EXPRESSION, expression
                    text_start = self._caret + expression_source_length + 1  # Start again right after the closing brace
                armed_at = False
            except (StopIteration, EOFError):
                if maybe_text := self._data[text_start:]:
                    yield self.TEXT, maybe_text
                break

    def _read_expression(self) -> t.Tuple[int, str]:
        """Use a tokenizer to detect the closing brace"""
        brace_depth: int = 0
        collected_tokens: t.List[str] = []
        tokenizer = ExpressionTokenizer(data=self._data[self._caret :])
        while True:
            token_info = tokenizer.get_token()
            if token_info.exact_type == tokenize.LBRACE:
                brace_depth += 1
            elif token_info.exact_type == tokenize.RBRACE:
                brace_depth -= 1
                if brace_depth < 0:
                    clean_expression: str = "".join(collected_tokens)
                    return tokenizer.position, clean_expression
            if token_info.exact_type not in self._IGNORED_TOKENS_TYPES:
                collected_tokens.append(token_info.string)


class Templar(LoggerMixin):
    """Expression renderer"""

    _LOOSE_OUTCOMES_RENDERING_DEFAULT_VALUE: str = ""

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
