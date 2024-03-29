# pylint: disable=missing-module-docstring,missing-class-docstring
from cjunct import ActionBase, ArgsBase


class DebugArgs(ArgsBase):
    message: str


class Action(ActionBase):
    args: DebugArgs

    async def run(self) -> None:
        self.emit(self.args.message)
