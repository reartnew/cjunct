"""Common strategy tests"""

import typing as t

import pytest

from cjunct.actions import ActionNet, ActionBase
from cjunct.strategy import LooseStrategy


@pytest.mark.asyncio
async def test_success(sample_net: ActionNet) -> None:
    """Check successful execution"""
    result: t.List[str] = []
    strategy: t.AsyncIterable[ActionBase] = LooseStrategy(sample_net)
    async for action in strategy:  # type: ActionBase
        action.get_future().set_result(None)
        result.append(action.name)
    assert result == ["foo", "bar"]
