from cjunct import ActionBase, ArgsBase, StringTemplate

__all__ = [
    "EchoAction",
    "EchoArgs",
]


class EchoArgs(ArgsBase):
    message: StringTemplate


class EchoAction(ActionBase):
    args: EchoArgs

    async def run(self) -> None:
        self.emit(self.args.message)
