"""Command-line interface entry"""

import sys
from pathlib import Path

import classlogging
import click
import dotenv

import cjunct
from cjunct.config.constants import C, CLI_PARAMS
from cjunct.exceptions import BaseError

logger = classlogging.get_module_logger()


@click.group
def main() -> None:
    """Entry group"""


@main.command
@click.option(
    "-d",
    "--directory",
    type=str,
    default="",
    help="Context directory. Defaults to current working directory",
)
@click.option(
    "-l",
    "--log-level",
    type=str,
    default="",
    help="Log level",
)
@click.pass_context
# pylint: disable=unused-argument
def run(ctx: click.Context, **kwargs) -> None:
    """Run pipeline immediately"""
    CLI_PARAMS.update(ctx.params)
    dotenv_path: Path = Path().resolve().parent / ".env"
    dotenv_loaded: bool = dotenv.load_dotenv(dotenv_path=dotenv_path)
    classlogging.configure_logging(level=C.LOG_LEVEL)
    if dotenv_loaded:
        logger.info(f"Loaded environment variables from {dotenv_path!r}")
    try:
        cjunct.Runner().run_sync()
    except BaseError as e:
        logger.debug("", exc_info=True)
        sys.stderr.write(f"! {e}\n")
        sys.exit(e.CODE)
    except Exception as e:
        logger.debug("", exc_info=True)
        sys.stderr.write(f"! UNHANDLED EXCEPTION: {e}\n")
        sys.exit(1)
