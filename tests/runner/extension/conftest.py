"""Extension test fixtures"""

from pathlib import Path

import pytest


@pytest.fixture
def echo_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prepare context dir for external action check"""
    (tmp_path / "network.yaml").write_bytes(
        b"""---
actions:
  - name: Foo
    type: echo
    message: foo
""",
    )
    monkeypatch.chdir(tmp_path)
