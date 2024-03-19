"""Shell action wrapped into a docker container"""

import asyncio
import contextlib
import tempfile
import typing as t
import uuid
from dataclasses import dataclass
from pathlib import Path

import aiodocker
from aiodocker.containers import DockerContainer

from ..base import EmissionScannerActionBase, ArgsBase
from ..types import StringTemplate, Stderr

__all__ = [
    "DockerShellArgs",
    "DockerShellAction",
]


@dataclass
class DockerBind:
    """Bind mount specification"""

    dest: StringTemplate
    src: t.Optional[StringTemplate] = None
    contents: t.Optional[StringTemplate] = None
    mode: str = "rw"

    def __post_init__(self) -> None:
        if self.contents is None and self.src is None:
            raise ValueError("Neither contents nor src specified")
        if self.contents is not None and self.src is not None:
            raise ValueError("Both contents and src specified")


class DockerShellArgs(ArgsBase):
    """Args for docker shell"""

    command: StringTemplate
    image: StringTemplate
    environment: t.Optional[t.Dict[str, StringTemplate]] = None
    cwd: t.Optional[str] = None
    pull: t.Optional[bool] = False
    executable: StringTemplate = "/bin/sh"  # type: ignore[assignment]
    bind: t.Optional[t.List[DockerBind]] = None


class DockerShellAction(EmissionScannerActionBase):
    """Docker shell commands handler"""

    args: DockerShellArgs
    _ENTRY_SCRIPT_FILE_NAME: str = "entry.sh"
    _CONTAINER_TMP_DIRECTORY: str = "/tmp"  # nosec

    @contextlib.asynccontextmanager
    async def _make_container(self, client: aiodocker.Docker) -> t.AsyncGenerator[DockerContainer, None]:
        container_name = f"cjunct-docker-shell-{uuid.uuid4().hex}"
        self.logger.info(f"Starting docker shell container {container_name!r}")
        with tempfile.TemporaryDirectory() as tmp_directory:
            tmp_dir_path: Path = Path(tmp_directory)
            script_container_directory: str = f"{self._CONTAINER_TMP_DIRECTORY}/{container_name}-exec-source"
            script_container_file: Path = tmp_dir_path / self._ENTRY_SCRIPT_FILE_NAME
            script_container_file_clauses: t.List[str] = [
                self._YIELD_SHELL_FUNCTION_DEFINITION,
                self.args.command,
            ]
            script_container_file.write_text(
                data="\n".join(script_container_file_clauses),
                encoding="utf-8",
            )
            container_binds: t.List[str] = [f"{tmp_directory}:{script_container_directory}:ro"]
            for bind_config in self.args.bind or []:
                if bind_config.src is not None:
                    container_binds.append(f"{bind_config.src}:{bind_config.dest}:{bind_config.mode}")
                elif bind_config.contents is not None:
                    bind_contents_file_local_path: Path = tmp_dir_path / uuid.uuid4().hex
                    bind_contents_file_local_path.write_text(
                        data=bind_config.contents,
                        encoding="utf-8",
                    )
                    container_binds.append(f"{bind_contents_file_local_path}:{bind_config.dest}:{bind_config.mode}")

            container: DockerContainer = await client.containers.run(
                name=container_name,
                config={
                    "Cmd": [self.args.executable, f"{script_container_directory}/{self._ENTRY_SCRIPT_FILE_NAME}"],
                    "Image": self.args.image,
                    "HostConfig": {"Binds": container_binds},
                    "Env": [f"{k}={v}" for k, v in (self.args.environment or {}).items()],
                    "WorkingDir": self.args.cwd,
                },
            )
            try:
                yield container
            finally:
                await container.delete(force=True)

    async def run(self) -> None:
        async with aiodocker.Docker() as client:
            if self.args.pull:
                self.logger.info(f"Pulling image: {self.args.image!r}")
                await client.pull(self.args.image)
            async with self._make_container(client) as container:
                tasks: t.List[asyncio.Task] = [
                    asyncio.create_task(self._read_stdout(container)),
                    asyncio.create_task(self._read_stderr(container)),
                ]
                await asyncio.gather(*tasks)
                result: dict = await container.wait()
                self.logger.debug(f"Docker container result: {result}")
                if (code := result.get("StatusCode", -1)) != 0:
                    self.fail(f"Exit code: {code}")

    async def _read_stdout(self, container: DockerContainer) -> None:
        async for chunk in container.log(stdout=True, follow=True):
            self.emit(chunk)

    async def _read_stderr(self, container: DockerContainer) -> None:
        async for chunk in container.log(stderr=True, follow=True):
            self.emit(Stderr(chunk))
