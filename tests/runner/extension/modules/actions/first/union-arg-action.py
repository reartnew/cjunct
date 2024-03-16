# pylint: disable=missing-module-docstring,missing-class-docstring,invalid-name
import typing as t

from cjunct import ActionBase, ArgsBase, StringTemplate


class UnionArgs(ArgsBase):
    message: t.Union[StringTemplate, t.List[StringTemplate]]


class Action(ActionBase):
    args: UnionArgs

    async def run(self) -> None:
        self.emit(str(self.args.message))
