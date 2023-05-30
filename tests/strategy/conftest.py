"""Loose strategy helpers"""

import pytest

from cjunct.actions import ActionNet, ActionBase, ActionDependency


@pytest.fixture
def sample_net() -> ActionNet:
    """Minimalistic action net"""
    return ActionNet(
        {
            "foo": ActionBase(name="foo"),
            "bar": ActionBase(name="bar", ancestors={"foo": ActionDependency()}),
        }
    )
