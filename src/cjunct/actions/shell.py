"""Separate module for shell-related action"""

import asyncio
import base64
import re
import textwrap
import typing as t

from async_shell import Shell, ShellResult

from .base import ActionBase, Stderr, ArgsBase, StringTemplate
from ..config.constants import C

__all__ = [
    "YIELD_FUNCTION_BOILERPLATE",
    "StreamScannerActionBase",
    "ShellArgs",
    "ShellAction",
]

YIELD_FUNCTION_BOILERPLATE: str = textwrap.dedent(
    """
        yield_outcome(){
          [ "$1" = "" ] && echo "Missing key (first argument)" && return 1
          command -v base64 >/dev/null || ( echo "Missing command: base64" && return 2 )
          [ "$2" = "" ] && value="$(cat /dev/stdin)" || value="$2"
          echo "##cjunct[yield-outcome-b64 $(printf "$1" | base64) $(printf "$value" | base64)]##"
          return 0
        }
    """
).lstrip()


# pylint: disable=abstract-method
class StreamScannerActionBase(ActionBase):
    """Base class for stream-scanning actions"""

    _YIELD_SCAN_PATTERN: t.ClassVar[t.Pattern] = re.compile(r"^(.*?)##cjunct\[yield-outcome-b64\s*(\S+)\s+(\S*)\s*]##$")

    async def _process_system_messages_in_stream(self, stream: t.AsyncIterable[str]) -> t.AsyncGenerator[str, None]:
        """Extract system messages from a stream"""
        # Store data prior to the system message
        memorized_prefix: str = ""
        async for line in stream:
            # `endswith` is a cheaper check than re.findall
            if line.endswith("]##") and (matches := self._YIELD_SCAN_PATTERN.findall(line)):
                try:
                    for preceding_content, encoded_key, encoded_value in matches:
                        memorized_prefix += preceding_content
                        self.logger.debug(f"Action {self.name!r} stream reported a key: {encoded_key!r}")
                        key: str = base64.b64decode(encoded_key, validate=True).decode()
                        value: str = base64.b64decode(encoded_value, validate=True).decode()
                        self.yield_outcome(key, value)
                except Exception:
                    self.logger.warning("Failed while parsing system message", exc_info=True)
            else:
                yield memorized_prefix + line
                memorized_prefix = ""
        # Do not forget to report system message prefix, if any
        if memorized_prefix:
            yield memorized_prefix


class ShellArgs(ArgsBase):
    """Args for shell-related actions"""

    command: t.Optional[StringTemplate] = None
    file: t.Optional[StringTemplate] = None
    environment: t.Optional[t.Dict[str, StringTemplate]] = None
    cwd: t.Optional[str] = None

    def __post_init__(self) -> None:
        if self.command is None and self.file is None:
            raise ValueError("Neither command nor file specified")
        if self.command is not None and self.file is not None:
            raise ValueError("Both command and file specified")


class ShellAction(StreamScannerActionBase):
    """Shell commands handler"""

    args: ShellArgs

    async def _read_stdout(self, shell_process: Shell) -> None:
        async for line in self._process_system_messages_in_stream(shell_process.read_stdout()):
            self.emit(line)

    async def _read_stderr(self, shell_process: Shell) -> None:
        async for line in shell_process.read_stderr():
            self.emit(Stderr(line))

    async def _create_shell(self) -> Shell:
        command: str = self.args.command or f"source '{self.args.file}'"
        if C.SHELL_INJECT_YIELD_FUNCTION:
            command = f"{YIELD_FUNCTION_BOILERPLATE}\n{command}"
        return Shell(
            command=command,
            environment=self.args.environment,  # type: ignore[arg-type]
            cwd=self.args.cwd,
        )

    async def run(self) -> None:
        async with await self._create_shell() as shell_process:
            tasks: t.List[asyncio.Task] = [
                asyncio.create_task(self._read_stdout(shell_process)),
                asyncio.create_task(self._read_stderr(shell_process)),
            ]
            await asyncio.gather(*tasks)
            result: ShellResult = await shell_process
            if result.code:
                self.fail(f"Exit code: {result.code}")
