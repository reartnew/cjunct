"""Separate module for shell-related action"""

import asyncio
import typing as t
from dataclasses import dataclass

from async_shell import Shell

from .base import ActionBase


@dataclass
class ShellAction(ActionBase):
    """Shell commands handler"""

    command: str = ""
    script: str = ""

    async def _read_stdout(self, shell_process: Shell):
        async for line in shell_process.read_stdout():
            self.emit(line)

    async def _read_stderr(self, shell_process: Shell):
        async for line in shell_process.read_stderr():
            self.emit(line)

    async def run(self) -> None:
        async with Shell(command=self.command) as shell_process:
            tasks: t.List[asyncio.Task] = [
                asyncio.create_task(self._read_stdout(shell_process)),
                asyncio.create_task(self._read_stderr(shell_process)),
            ]
            await asyncio.gather(*tasks)
            await shell_process.validate()
