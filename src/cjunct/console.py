"""Command-line interface entry"""

import sys
from pathlib import Path

import classlogging
import click
import dotenv

import cjunct
from cjunct.config.constants import C
from cjunct.config.constants.cli import cliargs_receiver
from cjunct.exceptions import BaseError

logger = classlogging.get_module_logger()


@click.group
@click.option("-d", "--directory", help="Context directory. Defaults to current working directory.")
@click.option("-l", "--log-level", help="Logging level. Defaults to 'ERROR.'")
@cliargs_receiver
def main() -> None:
    """Entry group"""


@main.command
@click.option("-s", "--strategy", help="Execution strategy name. Defaults to 'loose'.")
@cliargs_receiver
def run() -> None:
    """Run pipeline immediately."""
    dotenv_path: Path = Path().resolve().parent / ".env"
    dotenv_loaded: bool = dotenv.load_dotenv(dotenv_path=dotenv_path)
    classlogging.configure_logging(level=C.LOG_LEVEL)
    if dotenv_loaded:
        logger.info(f"Loaded environment variables from {dotenv_path!r}")
    try:
        cjunct.Runner(strategy_class=C.STRATEGY_CLASS).run_sync()
    except BaseError as e:
        logger.debug("", exc_info=True)
        sys.stderr.write(f"! {e}\n")
        sys.exit(e.CODE)
    except Exception as e:
        logger.debug("", exc_info=True)
        sys.stderr.write(f"! UNHANDLED EXCEPTION: {e}\n")
        sys.exit(1)
