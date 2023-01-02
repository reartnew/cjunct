import typing as t

from .process import AsyncSubprocess, SubprocessResult

__all__ = [
    "ShellCommand",
]


class ShellCommand:
    """Shell action resolver"""

    def __init__(self, action) -> None:
        self._action = action
        self.succeeded: bool = False

    async def run(self) -> t.AsyncGenerator[str, None]:
        """Initialize a process and run through its streams"""

        async with AsyncSubprocess(self._action.command) as proc:
            async for line in proc.read_stdout():
                yield line
            result: SubprocessResult = await proc
        self.succeeded = not result.code
