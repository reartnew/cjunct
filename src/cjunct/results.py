"""Action results manipulation proxies"""

import re
import typing as t

ActionResultDataType = t.Dict[str, t.Any]
ActionsResultsContainerDataType = t.Dict[str, ActionResultDataType]

__all__ = [
    "ActionResultDataType",
    "ActionsResultsContainerDataType",
    "ActionResultReadOnlyProxy",
    "ResultsProxy",
]


class ActionResultReadOnlyProxy:
    """Single action's result holder"""

    DEFAULT: str = ""

    def __init__(self, actual_action_result: ActionResultDataType) -> None:
        self._data: ActionResultDataType = actual_action_result

    def __getitem__(self, item: str) -> t.Any:
        return self._data.get(item, self.DEFAULT)


class ResultsProxy:
    """Map action names to result holders and perform templating"""

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

    def __init__(self, actual_actions_results_collection: ActionsResultsContainerDataType) -> None:
        self._data: ActionsResultsContainerDataType = actual_actions_results_collection

    def __getitem__(self, item: str) -> ActionResultReadOnlyProxy:
        return ActionResultReadOnlyProxy(self._data.get(item, {}))

    def _replace(self, match: t.Match) -> str:
        prior: str = match.groupdict()["prior"]
        expression: str = match.groupdict()["expression"]
        parts: t.List[str] = expression.split(".", maxsplit=1)
        action_name, key = parts
        value = self[action_name][key]
        return f"{prior}{value}"

    def substitute(self, data: str) -> str:
        """Process string data, replacing all @{} occurrences"""
        return self._TEMPLATE_SUBST_PATTERN.sub(self._replace, data)
