"""Check action parsing"""

import asyncio
import typing as t

import pytest

from cjunct.actions import ActionBase


class TestAction(ActionBase):
    """A stub."""

    MESSAGES = [
        "Foo",
        "Bar",
        "Baz",
    ]

    def __init__(self) -> None:
        super().__init__(name="test", type="test")

    async def run(self):
        for message in self.MESSAGES:
            self.emit(message)
            await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_action_emitter():
    """Check messages handling"""
    action = TestAction()
    events: t.List[str] = []

    async def reader():
        async for event in action.read_events():
            events.append(event)

    reader_task = asyncio.create_task(reader())
    await action
    await reader_task
    assert events == TestAction.MESSAGES


@pytest.mark.asyncio
async def test_action_await_twice():
    """Check multiple awaiting"""
    action = TestAction()
    await action
    await action
