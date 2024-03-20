"""Command-line interface entry"""

import functools
import sys
from pathlib import Path

import classlogging
import click
import dotenv

import cjunct
from cjunct.config.constants import C, LOG_LEVELS
from cjunct.config.constants.cli import cliargs_receiver
from cjunct.exceptions import BaseError, ExecutionFailed

logger = classlogging.get_module_logger()


@click.group
@click.option("-d", "--directory", help="Context directory. Defaults to current working directory.")
@click.option("-l", "--log-level", help="Logging level. Defaults to ERROR.", type=click.Choice(list(LOG_LEVELS)))
@click.option("-f", "--file", help="Action file to execute.")
@cliargs_receiver
def main() -> None:
    """Declarative parallel process runner"""


def wrap_cli_command(func):
    """Standard loading and error handling"""

    @main.command
    @cliargs_receiver
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        dotenv_path: Path = Path().resolve() / ".env"
        dotenv_loaded: bool = dotenv.load_dotenv(dotenv_path=dotenv_path)
        classlogging.configure_logging(level=C.LOG_LEVEL, colorize=C.USE_COLOR)
        if dotenv_loaded:
            logger.info(f"Loaded environment variables from {dotenv_path!r}")
        else:
            logger.debug(f"Dotenv not found: {dotenv_path!r}")
        try:
            return func(*args, **kwargs)
        except BaseError as e:
            logger.debug("", exc_info=True)
            sys.stderr.write(f"! {e}\n")
            sys.exit(e.CODE)
        except ExecutionFailed:
            logger.debug("Some steps failed")
            sys.exit(1)
        except Exception as e:
            logger.debug("", exc_info=True)
            sys.stderr.write(f"! UNHANDLED EXCEPTION: {e!r}\n")
            sys.exit(2)

    return wrapped


@wrap_cli_command
@click.option("-s", "--strategy", help="Execution strategy name. Defaults to 'loose'.")
@click.option("-i", "--interactive", help="Run in interactive mode.", is_flag=True, default=False)
def run() -> None:
    """Run pipeline immediately."""
    cjunct.Runner(
        strategy_class=C.STRATEGY_CLASS,
        display_class=C.DISPLAY_CLASS,
    ).run_sync()


@wrap_cli_command
def validate() -> None:
    """Check configuration validity."""
    action_num: int = len(
        cjunct.Runner(
            strategy_class=C.STRATEGY_CLASS,
            display_class=C.DISPLAY_CLASS,
        ).actions
    )
    logger.info(f"Located actions number: {action_num}")
