"""Separate module for shell-related action"""

from async_shell import Shell

from .base import ActionBase


class ShellAction(ActionBase):
    """Shell commands handler"""

    async def run(self) -> None:
        shell_process: Shell = Shell(command=self.command)
        async for line in shell_process.read_stdout():
            self.emit(line)
        await shell_process.validate()
