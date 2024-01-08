"""Separate module for shell-related action"""

import asyncio
import base64
import re
import textwrap
import typing as t
from dataclasses import dataclass, field

from async_shell import Shell

from .base import ActionBase, Stderr
from ..config.constants import C
from ..results import ResultsProxy


@dataclass
class ShellAction(ActionBase):
    """Shell commands handler"""

    command: str = ""
    script: str = ""
    result: t.Dict[str, str] = field(default_factory=dict, init=False, repr=False)

    YIELD_SCANNER_PATTERN: t.ClassVar[t.Pattern] = re.compile(r"^(.*?)##cjunct\[yield-b64\s*(\S+)\s+(\S*)\s*]##$")
    YIELD_FUNCTION_BOILERPLATE: t.ClassVar[str] = textwrap.dedent(
        """
            yield(){
              [ "$1" = "" ] && echo "Missing key (first argument)" && return 1
              command -v base64 >/dev/null || ( echo "Missing command: base64" && return 2 )
              [ "$2" = "" ] && value="$(cat /dev/stdin)" || value="$2"
              echo "##cjunct[yield-b64 $(printf "$1" | base64) $(printf "$value" | base64)]##"
              return 0
            }
            export -f yield"""
    ).lstrip()

    async def _read_stdout(self, shell_process: Shell):
        # Store data prior to the system message
        memorized_prefix: str = ""
        async for line in shell_process.read_stdout():
            # `endswith` is a cheaper check than re.findall
            if line.endswith("]##") and (matches := self.YIELD_SCANNER_PATTERN.findall(line)):
                try:
                    for preceding_content, encoded_key, encoded_value in matches:
                        memorized_prefix += preceding_content
                        self.logger.debug(f"Shell action {self.name!r} reported a key: {encoded_key!r}")
                        key: str = base64.b64decode(encoded_key).decode()
                        value: str = base64.b64decode(encoded_value).decode()
                        self.result[key] = value
                except Exception:
                    self.logger.warning("Failed while parsing system message", exc_info=True)
            else:
                self.emit(memorized_prefix + line)
                memorized_prefix = ""

        # Do not forget to report system message prefix, if any
        if memorized_prefix:
            self.emit(memorized_prefix)

    async def _read_stderr(self, shell_process: Shell):
        async for line in shell_process.read_stderr():
            self.emit(Stderr(line))

    def _make_command(self) -> str:
        command: str = self.command or f"source '{self.script}'"
        if C.SHELL_INJECT_YIELD_FUNCTION:
            command = f"{self.YIELD_FUNCTION_BOILERPLATE}\n{command}"
        return command

    async def run(self) -> t.Dict[str, str]:
        async with Shell(command=self._make_command()) as shell_process:
            tasks: t.List[asyncio.Task] = [
                asyncio.create_task(self._read_stdout(shell_process)),
                asyncio.create_task(self._read_stderr(shell_process)),
            ]
            await asyncio.gather(*tasks)
            await shell_process.validate()
        return self.result

    async def warmup(self, results: ResultsProxy) -> None:
        self.command = results.substitute(data=self.command)
        await super().warmup(results)
