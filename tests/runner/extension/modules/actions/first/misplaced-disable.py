# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name
from cjunct import ActionBase


class Action(ActionBase):

    async def run(self) -> None:
        self.disable()
