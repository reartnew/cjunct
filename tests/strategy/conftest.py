"""Loose strategy helpers"""

# pylint: disable=redefined-outer-name

import typing as t

import pytest

from cjunct.actions import ActionNet, ActionBase, ActionDependency


def _make_chained_net(action_class: t.Type[ActionBase]) -> ActionNet:
    step_names: t.List[str] = [
        "foo",
        "bar",
        "baz",
        "qux",
        "fred",
        "thud",
    ]
    return ActionNet(
        {
            step_name: action_class(
                name=step_name,
                ancestors={step_names[num - 1]: ActionDependency(strict=True)} if num else {},
            )
            for num, step_name in enumerate(step_names)
        }
    )


@pytest.fixture
def strict_successful_net() -> ActionNet:
    """Minimalistic strict chained action net"""

    class SuccessAction(ActionBase[None]):
        """Does nothing"""

        async def run(self) -> None:
            pass

    return _make_chained_net(action_class=SuccessAction)


@pytest.fixture
def strict_failing_net() -> ActionNet:
    """Minimalistic strict chained action net with failures"""

    class FailingAction(ActionBase[None]):
        """Raises RuntimeError"""

        async def run(self) -> None:
            raise RuntimeError

    return _make_chained_net(action_class=FailingAction)


@pytest.fixture
def strict_skipping_net() -> ActionNet:
    """Minimalistic strict chained action net with explicit skipping"""

    class SkippingAction(ActionBase[None]):
        """Raises RuntimeError"""

        async def run(self) -> None:
            self.skip()

    return _make_chained_net(action_class=SkippingAction)
