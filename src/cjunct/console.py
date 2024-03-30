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
from cjunct.config.environment import Env
from cjunct.exceptions import BaseError, ExecutionFailed
from cjunct.strategy import KNOWN_STRATEGIES

logger = classlogging.get_module_logger()


@click.group
@click.option(
    "-d",
    "--directory",
    help="Context directory. Defaults to current working directory. "
    "Also configurable via the CJUNCT_CONTEXT_DIRECTORY environment variable.",
)
@click.option(
    "-l",
    "--log-level",
    help="Logging level. Defaults to ERROR. Also configurable via the CJUNCT_LOG_LEVEL environment variable.",
    type=click.Choice(list(LOG_LEVELS)),
)
@click.option(
    "-f",
    "--file",
    help="Workflow file. Use '-' value to read yaml configuration from the standard input. "
    "When not given, will look for one of cjunct.yml/cjunct.yaml files in the context directory. "
    "Also configurable via the CJUNCT_WORKFLOW_FILE environment variable.",
)
@cliargs_receiver
def main() -> None:
    """Declarative task runner"""


def wrap_cli_command(func):
    """Standard loading and error handling"""

    @main.command
    @cliargs_receiver
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        dotenv_path: Path = C.ENV_FILE
        dotenv_loaded: bool = dotenv.load_dotenv(dotenv_path=dotenv_path)
        classlogging.configure_logging(
            level=C.LOG_LEVEL,
            colorize=C.USE_COLOR and not C.LOG_FILE,
            main_file=C.LOG_FILE,
            stream=None if C.LOG_FILE else classlogging.LogStream.STDERR,
        )
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
@click.option(
    "-s",
    "--strategy",
    help="Execution strategy. Defaults to loose. Also configurable via the CJUNCT_STRATEGY_NAME environment variable.",
    type=click.Choice(list(KNOWN_STRATEGIES)),
)
@click.option("-i", "--interactive", help="Run in dialog mode.", is_flag=True, default=False)
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


@main.group
def info() -> None:
    """Package information."""


@info.command
def version() -> None:
    """Show package version."""
    print(cjunct.__version__)


@info.command
def env_vars() -> None:
    """Show environment variables that are taken into account."""
    print(Env.__doc__)
