"""ActionNet dedicated module"""

from __future__ import annotations

import typing as t

from classlogging import LoggerMixin

from ..actions.base import Action
from ..exceptions import IntegrityError

__all__ = [
    "ActionNet",
]


class ActionNet(t.Dict[str, Action], LoggerMixin):
    """Action relations map"""

    def __init__(self, net: dict[str, Action], checklists: t.Dict[str, t.List[str]] | None = None) -> None:
        super().__init__(net)
        self.entrypoints: t.Set[str] = set()
        self.checklists: t.Dict[str, t.List[str]] = checklists or {}
        # Check dependencies integrity
        self._establish_descendants()
        # Now go Dijkstra
        self._allocate_tiers()

    def _establish_descendants(self) -> None:
        missing_non_external_deps: t.Set[str] = set()
        for action in self.values():  # type: Action
            for dependency_action_name, dependency in list(action.ancestors.items()):
                if dependency_action_name not in self:
                    if dependency.external:
                        # Get rid of missing external deps
                        action.ancestors.pop(dependency_action_name)
                    else:
                        missing_non_external_deps.add(dependency_action_name)
                    continue
                # Register symmetric descendant connection for further simplicity
                self[dependency_action_name].descendants[action.name] = dependency
            # Check if there are any dependencies after removal at all
            if not action.ancestors:
                self.entrypoints.add(action.name)
        if missing_non_external_deps:
            raise IntegrityError(f"Missing actions among dependencies: {sorted(missing_non_external_deps)}")
        # Check entrypoints presence
        if not self.entrypoints:
            raise IntegrityError("No entrypoints for the graph")

    def _allocate_tiers(self) -> None:
        step_tier: int = 1
        tier_actions_names: t.Set[str] = self.entrypoints
        while True:
            next_tier_actions_names: t.Set[str] = set()
            for tier_action_name in tier_actions_names:
                tier_action: Action = self[tier_action_name]
                if tier_action.tier is not None:
                    continue
                tier_action.tier = step_tier
                next_tier_actions_names |= set(tier_action.descendants)
            if not next_tier_actions_names:
                break
            step_tier += 1
            tier_actions_names = next_tier_actions_names
        self.logger.debug(f"Number of tiers: {step_tier}")
        unreachable_action_names: t.Set[str] = {action.name for action in self.values() if action.tier is None}
        if unreachable_action_names:
            raise IntegrityError(f"Unreachable actions found: {sorted(unreachable_action_names)}")

    def __str__(self) -> str:
        """Return tree representation of the action graph"""
        return str(self)
