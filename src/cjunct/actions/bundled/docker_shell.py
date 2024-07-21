"""Shell action wrapped into a docker container"""

import asyncio
import contextlib
import functools
import tempfile
import typing as t
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import aiodocker
import aiohttp
from aiodocker.containers import DockerContainer
from aiohttp.client import DEFAULT_TIMEOUT

from ..base import EmissionScannerActionBase, ArgsBase
from ..types import Stderr
from ...config.constants import C

__all__ = [
    "DockerShellArgs",
    "DockerShellAction",
]


class BindMode(Enum):
    """Allowed bind mount modes"""

    READ_ONLY = "ro"
    READ_WRITE = "rw"


class NetworkMode(Enum):
    """Allowed network modes"""

    BRIDGE = "bridge"
    HOST = "host"
    NONE = "none"


@dataclass
class Auth:
    """Docker auth info"""

    username: str
    password: str
    hostname: t.Optional[str] = None


@dataclass
class Network:
    """Container network specification"""

    mode: NetworkMode = NetworkMode.BRIDGE


@dataclass
class FileDockerBind:
    """File-based bind mount specification"""

    src: str
    dest: str
    mode: BindMode = BindMode.READ_WRITE


@dataclass
class ContentDockerBind:
    """Content-based bind mount specification"""

    contents: str
    dest: str
    mode: BindMode = BindMode.READ_ONLY


class DockerShellArgs(ArgsBase):
    """Args for docker shell"""

    command: str
    image: str
    environment: t.Optional[t.Dict[str, str]] = None
    cwd: t.Optional[str] = None
    pull: bool = False
    executable: str = "/bin/sh"
    bind: t.Optional[t.List[t.Union[FileDockerBind, ContentDockerBind]]] = None
    network: Network = field(default_factory=Network)  # pylint: disable=invalid-field-call
    privileged: bool = False
    auth: t.Optional[Auth] = None


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
                self.args.command,
            ]
            if C.SHELL_INJECT_YIELD_FUNCTION:
                script_container_file_clauses.insert(0, self._SHELL_SERVICE_FUNCTIONS_DEFINITIONS)
            script_container_file.write_text(
                data="\n".join(script_container_file_clauses),
                encoding="utf-8",
            )
            container_binds: t.List[str] = [f"{tmp_directory}:{script_container_directory}:ro"]
            for bind_config in self.args.bind or []:
                if isinstance(bind_config, FileDockerBind):
                    container_binds.append(f"{bind_config.src}:{bind_config.dest}:{bind_config.mode.value}")
                else:
                    bind_contents_local_file: Path = tmp_dir_path / uuid.uuid4().hex
                    bind_contents_local_file.write_text(
                        data=bind_config.contents,
                        encoding="utf-8",
                    )
                    container_binds.append(f"{bind_contents_local_file}:{bind_config.dest}:{bind_config.mode.value}")

            container: DockerContainer = await client.containers.run(
                name=container_name,
                config={
                    "Cmd": [self.args.executable, f"{script_container_directory}/{self._ENTRY_SCRIPT_FILE_NAME}"],
                    "Image": self.args.image,
                    "HostConfig": {
                        "Binds": container_binds,
                        "Init": True,
                        "NetworkMode": self.args.network.mode.value,
                    },
                    "Env": [f"{k}={v}" for k, v in (self.args.environment or {}).items()],
                    "WorkingDir": self.args.cwd,
                    "Privileged": self.args.privileged,
                },
                auth=self._make_auth(),
            )
            try:
                yield container
            finally:
                await container.delete(force=True)

    @functools.lru_cache(maxsize=1)
    def _make_auth(self) -> t.Optional[t.Dict[str, str]]:
        if self.args.auth is None:
            return None
        auth_dict: t.Dict[str, str] = {
            "username": self.args.auth.username,
            "password": self.args.auth.password,
        }
        if self.args.auth.hostname is not None:
            auth_dict["serveraddress"] = self.args.auth.hostname
        return auth_dict

    async def run(self) -> None:
        async with aiodocker.Docker() as client:
            # Enable default timeout for the connect phase only
            # pylint: disable=protected-access
            client.session._timeout = aiohttp.ClientTimeout(
                connect=DEFAULT_TIMEOUT.total,
            )
            if self.args.pull:
                self.logger.info(f"Pulling image: {self.args.image!r}")
                await client.pull(
                    from_image=self.args.image,
                    auth=self._make_auth(),
                )
            async with self._make_container(client) as container:
                tasks: t.List[asyncio.Task] = [
                    asyncio.create_task(self._read_stdout(container)),
                    asyncio.create_task(self._read_stderr(container)),
                ]
                # Wait for all tasks to complete
                await asyncio.wait(tasks)
                # Check exceptions
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
