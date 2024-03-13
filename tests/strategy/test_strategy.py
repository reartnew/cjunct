"""Common strategy tests"""

import collections
import typing as t

import pytest

from cjunct import ActionBase, LooseStrategy
from cjunct.actions.base import ActionStatus
from cjunct.actions.net import ActionNet


@pytest.mark.asyncio
async def test_chain_success(strict_successful_net: ActionNet) -> None:
    """Chain successful execution"""
    result: t.List[ActionBase] = []
    strategy: t.AsyncIterable[ActionBase] = LooseStrategy(strict_successful_net)
    async for action in strategy:  # type: ActionBase
        await action
        result.append(action)
    assert len(result) == 6  # Should emit all actions
    assert all(action.status == ActionStatus.SUCCESS for action in result)


@pytest.mark.asyncio
async def test_chain_failure(strict_failing_net: ActionNet) -> None:
    """Chain failing execution"""
    result: t.List[ActionBase] = []
    strategy: t.AsyncIterable[ActionBase] = LooseStrategy(strict_failing_net)
    async for action in strategy:  # type: ActionBase
        with pytest.raises(RuntimeError):
            await action
        result.append(action)
    assert len(result) == 1  # Should not emit more than one action
    assert result[0].status == ActionStatus.FAILURE
    # Check final states now
    assert collections.Counter(a.status for a in strict_failing_net.values()) == {
        ActionStatus.FAILURE: 1,
        ActionStatus.SKIPPED: 5,
    }


@pytest.mark.asyncio
async def test_chain_skip(strict_skipping_net: ActionNet) -> None:
    """Chain skipping execution"""
    result: t.List[ActionBase] = []
    strategy: t.AsyncIterable[ActionBase] = LooseStrategy(strict_skipping_net)
    async for action in strategy:  # type: ActionBase
        await action
        result.append(action)
    assert len(result) == 1  # Should not emit more than one action
    assert result[0].status == ActionStatus.SKIPPED
    # Check final states now
    assert all(a.status == ActionStatus.SKIPPED for a in strict_skipping_net.values())


def test_non_redefined_name() -> None:
    """Check strategy name collision"""
    with pytest.raises(NameError, match="Strategy named 'loose' already exists"):
        # pylint: disable=unused-variable
        class NewLooseStrategy(LooseStrategy):
            """Do not define new name"""
