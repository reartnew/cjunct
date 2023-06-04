"""Loose strategy helpers"""

import pytest

from cjunct.actions import ActionNet, ActionBase, ActionDependency


@pytest.fixture
def strict_net() -> ActionNet:
    """Minimalistic strict action net"""
    return ActionNet(
        {
            "foo": ActionBase(name="foo"),
            "bar": ActionBase(name="bar", ancestors={"foo": ActionDependency(strict=True)}),
        }
    )
