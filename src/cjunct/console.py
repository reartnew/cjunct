"""Command-line interface entry"""

import logging
import sys
import typing as t
from pathlib import Path

import classlogging
import click
import dotenv

import cjunct
from cjunct.config.constants import C
from cjunct.config.constants.cli import cliargs_receiver
from cjunct.exceptions import BaseError

logger = classlogging.get_module_logger()
_log_levels: t.Sequence[str] = list(logging._nameToLevel)  # pylint: disable=protected-access


@click.group
@click.option("-d", "--directory", help="Context directory. Defaults to current working directory.")
@click.option("-l", "--log-level", help="Logging level. Defaults to ERROR.", type=click.Choice(_log_levels))
@click.option("-f", "--file", help="Action file to execute.")
@cliargs_receiver
def main() -> None:
    """Entry group"""


@main.command
@click.option("-s", "--strategy", help="Execution strategy name. Defaults to 'loose'.")
@cliargs_receiver
def run() -> None:
    """Run pipeline immediately."""
    dotenv_path: Path = Path().resolve() / ".env"
    dotenv_loaded: bool = dotenv.load_dotenv(dotenv_path=dotenv_path)
    classlogging.configure_logging(level=C.LOG_LEVEL)
    if dotenv_loaded:
        logger.info(f"Loaded environment variables from {dotenv_path!r}")
    else:
        logger.debug(f"Dotenv not found: {dotenv_path!r}")
    try:
        cjunct.Runner(
            strategy_class=C.STRATEGY_CLASS,
            display_class=C.DISPLAY_CLASS,
        ).run_sync()
    except BaseError as e:
        logger.debug("", exc_info=True)
        sys.stderr.write(f"! {e}\n")
        sys.exit(e.CODE)
    except Exception as e:
        logger.debug("", exc_info=True)
        sys.stderr.write(f"! UNHANDLED EXCEPTION: {e}\n")
        sys.exit(1)
