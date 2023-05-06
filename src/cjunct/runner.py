import asyncio
import typing as t
from pathlib import Path

import classlogging

from .actions import ActionNet, Action
from .config.loaders import get_default_loader_class_for_file
from .config.loaders.base import BaseConfigLoader
from .display import NetPrefixDisplay, BaseDisplay
from .exceptions import SourceError
from .strategy import BaseStrategy, LooseStrategy

LoaderClassType = t.Type[BaseConfigLoader]
StrategyClassType = t.Type[BaseStrategy]

__all__ = [
    "Runner",
]


class Runner(classlogging.LoggerMixin):
    """Main entry object"""

    def __init__(
        self,
        config: t.Union[str, Path, None] = None,
        loader_class: t.Optional[LoaderClassType] = None,
        strategy_class: StrategyClassType = LooseStrategy,
    ) -> None:
        self._config_path: Path = self._detect_config_source() if config is None else Path(config)
        self._loader_class: LoaderClassType = loader_class or get_default_loader_class_for_file(self._config_path)
        self.logger.debug(f"Using config loader class: {self._loader_class}")
        self._strategy_class: StrategyClassType = strategy_class
        self.logger.debug(f"Using strategy class: {self._strategy_class}")

    @classmethod
    def _detect_config_source(cls) -> Path:
        scan_path: Path = Path().absolute()
        cls.logger.debug(f"Looking for config files at {scan_path}")
        if (maybe_xml := scan_path / "network.xml").exists():
            cls.logger.info(f"Detected config source: {maybe_xml}")
            return maybe_xml
        raise SourceError(f"No config source detected in {scan_path}")

    async def run_async(self):
        """Primary coroutine for all further processing"""
        actions: ActionNet = self._loader_class().load(self._config_path)
        display: BaseDisplay = NetPrefixDisplay(net=actions)
        strategy: BaseStrategy = self._strategy_class(net=actions)
        action_readers: t.List[asyncio.Task] = []
        async for action in strategy:  # type: Action
            self.logger.trace(f"Allocating action iterator for {action.name!r}")
            action_readers.append(asyncio.create_task(self._iterate_through_action(action=action, display=display)))
        for reader in action_readers:
            await reader

    @staticmethod
    async def _iterate_through_action(action: Action, display: BaseDisplay) -> None:
        async for message in action.run():
            display.emit(source=action.name, message=message)

    def run_sync(self):
        """Wrap async run into an event loop"""
        asyncio.run(self.run_async())
