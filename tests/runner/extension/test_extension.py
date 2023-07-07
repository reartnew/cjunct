"""Check extension possibilities"""

import typing as t
from dataclasses import dataclass
from pathlib import Path

import pytest

from cjunct import Runner
from cjunct.actions import ActionBase
from cjunct.config.loaders import DefaultYAMLConfigLoader


@dataclass
class EchoAction(ActionBase[None]):
    """Simple printer"""

    message: str = ""

    async def run(self) -> None:
        """Show message via display"""
        self.emit(self.message)


class ExtensionYAMLConfigLoader(DefaultYAMLConfigLoader):
    """Able to build echoes"""

    ACTION_FACTORIES = {**DefaultYAMLConfigLoader.ACTION_FACTORIES, "echo": EchoAction}

    def _build_action_from_dict(self, node: dict) -> ActionBase:
        action: ActionBase = super()._build_action_from_dict(node)
        # Varying args for echo
        if isinstance(action, EchoAction):
            action.message = self._parse_string_attr(attrib_name="message", node=node)
            if not action.message:
                self._throw(f"Action {action.name!r} message not specified")
        return action


class ExtensionRunner(Runner):
    """Use custom loader"""

    def __init__(self) -> None:
        super().__init__(loader_class=ExtensionYAMLConfigLoader)


def test_extended_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, display_collector: t.List[str]) -> None:
    """Validate custom loader"""
    (tmp_path / "network.yaml").write_bytes(
        b"""---
actions:
  - name: Foo
    type: echo
    message: foo
""",
    )
    monkeypatch.chdir(tmp_path)
    ExtensionRunner().run_sync()
    assert display_collector == [
        "[Foo] | foo",
        "============",
        "SUCCESS: Foo",
    ]
