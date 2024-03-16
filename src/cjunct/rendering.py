"""
Runner has too many dependencies,
thus placed to a separate module.
"""

import os
import re
import shlex
import typing as t

from classlogging import LoggerMixin

from .actions.base import RenderedStringTemplate
from .config.constants import C
from .exceptions import ActionRenderError

__all__ = [
    "Templar",
]


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
