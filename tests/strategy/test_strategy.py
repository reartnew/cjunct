"""Common strategy tests"""

import typing as t

import pytest

from cjunct.actions import ActionNet, ActionBase
from cjunct.strategy import LooseStrategy


@pytest.mark.asyncio
async def test_success(strict_net: ActionNet) -> None:
    """Check successful execution"""
    result: t.List[str] = []
    strategy: t.AsyncIterable[ActionBase] = LooseStrategy(strict_net)
    async for action in strategy:  # type: ActionBase
        # Simulate success
        action.get_future().set_result(None)
        result.append(action.name)
    assert result == ["foo", "bar"]


@pytest.mark.asyncio
async def test_total_failure(strict_net: ActionNet) -> None:
    """Check failing execution"""
    result: t.List[str] = []
    strategy: t.AsyncIterable[ActionBase] = LooseStrategy(strict_net)
    async for action in strategy:  # type: ActionBase
        # Simulate failure
        action.get_future().set_exception(Exception)
        result.append(action.name)
    assert result == ["foo"]
