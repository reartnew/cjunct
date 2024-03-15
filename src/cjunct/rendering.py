"""
Runner has too many dependencies,
thus placed to a separate module.
"""

import os
import re
import shlex
import typing as t

from .actions.base import RenderedStringTemplate
from .exceptions import ActionRenderError

__all__ = [
    "Templar",
]


class Templar:
    """Expression renderer"""

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
        outcome_getter: t.Callable[[str, str], t.Optional[str]],
        status_getter: t.Callable[[str], t.Optional[str]],
        raw_context_getter: t.Callable[[str], t.Optional[str]],
    ) -> None:
        self._outcome_getter = outcome_getter
        self._status_getter = status_getter
        self._raw_context_getter = raw_context_getter

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
        part_type, *other_parts = self._string_template_expression_split(expression)
        if part_type == "outcomes":
            if len(other_parts) != 2:
                raise ActionRenderError(f"Outcomes expression has {len(other_parts) + 1} parts of 3: {expression!r}")
            action_name, key = other_parts
            if (outcome := self._outcome_getter(action_name, key)) is None:
                raise ActionRenderError(f"Outcome {key!r} not found for action {action_name!r} (from {expression!r})")
            return outcome
        if part_type == "status":
            if len(other_parts) != 1:
                raise ActionRenderError(f"Status expression has {len(other_parts) + 1} parts of 2: {expression!r}")
            (action_name,) = other_parts
            if (action_status := self._status_getter(action_name)) is None:
                raise ActionRenderError(f"Action not found: {action_status!r}")
            return action_status
        if part_type == "environment":
            if len(other_parts) != 1:
                raise ActionRenderError(f"Environment expression has {len(other_parts) + 1} parts of 2: {expression!r}")
            (variable_name,) = other_parts
            return os.getenv(variable_name, "")
        if part_type == "context":
            if len(other_parts) != 1:
                raise ActionRenderError(f"Context expression has {len(other_parts) + 1} parts of 2: {expression!r}")
            (context_key,) = other_parts
            if (raw_context_value := self._raw_context_getter(context_key)) is None:
                raise ActionRenderError(f"Context key not found: {context_key!r}")
            return self.render(raw_context_value)
        raise ActionRenderError(f"Unknown expression type: {part_type!r} (from {expression!r})")
