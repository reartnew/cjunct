"""Separate module for shell-related action"""

import asyncio
import textwrap
import typing as t
from dataclasses import dataclass

from async_shell import Shell

from .base import ActionBase, Stderr
from ..config.constants import C


@dataclass
class ShellAction(ActionBase):
    """Shell commands handler"""

    command: str = ""
    script: str = ""
    YIELD_FUNCTION_BOILERPLATE: t.ClassVar[str] = textwrap.dedent(
        """
            yield(){
              [ "$1" = "" ] && echo "Missing key (first argument)" && exit 1
              command -v base64 >/dev/null || ( echo "Missing command: base64" && exit 2 )
              [ "$2" = "" ] && value="$(cat /dev/stdin)" || value="$2"
              echo "##cjunct[yield $(printf "$1" | base64) $(printf "$value" | base64)]"
              exit 0
            }
            export -f yield"""
    ).lstrip()

    async def _read_stdout(self, shell_process: Shell):
        async for line in shell_process.read_stdout():
            self.emit(line)

    async def _read_stderr(self, shell_process: Shell):
        async for line in shell_process.read_stderr():
            self.emit(Stderr(line))

    def _make_command(self) -> str:
        command: str = self.command or f"source '{self.script}'"
        if C.SHELL_INJECT_YIELD_FUNCTION:
            command = f"{self.YIELD_FUNCTION_BOILERPLATE}\n{command}"
        return command

    async def run(self) -> None:
        async with Shell(command=self._make_command()) as shell_process:
            tasks: t.List[asyncio.Task] = [
                asyncio.create_task(self._read_stdout(shell_process)),
                asyncio.create_task(self._read_stderr(shell_process)),
            ]
            await asyncio.gather(*tasks)
            await shell_process.validate()
