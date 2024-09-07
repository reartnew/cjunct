"""Command-line interface entry"""

import functools
import os
import sys
import typing as t
from pathlib import Path

import classlogging
import click
from dotenv.main import DotEnv

import cjunct
from cjunct.config.constants import C, LOG_LEVELS
from cjunct.config.constants.cli import cliargs_receiver
from cjunct.config.environment import Env
from cjunct.exceptions import BaseError, ExecutionFailed
from cjunct.strategy import KNOWN_STRATEGIES
from cjunct.tools.proxy import DeferredCallsProxy
from cjunct.display.default import KNOWN_DISPLAYS

logger = DeferredCallsProxy(obj=classlogging.get_module_logger())


class WorkflowPositionalArgument(click.Argument):
    """Optional positional argument for the workflow source"""

    NAME: str = "WORKFLOW"

    def __init__(self, param_decls: t.Sequence[str], required: t.Optional[bool] = None, **attrs: t.Any) -> None:
        if attrs or required is not None:
            self._throw("Cannot apply any attributes")
        super().__init__(param_decls, required=False, nargs=-1)

    def get_help_record(self, ctx: click.Context) -> t.Optional[t.Tuple[str, str]]:
        return self.make_metavar(), (
            "Workflow source file. When not given, will look for one of cjunct.yml/cjunct.yaml "
            "files in the context directory. Use the '-' value to read yaml configuration from the standard input. "
            "Also configurable via the CJUNCT_WORKFLOW_FILE environment variable."
        )

    def process_value(self, ctx: click.Context, value: t.Any) -> t.Optional[str]:
        """Check that there is not more than one argument for the workflow source"""
        vanilla_value: t.Tuple[str, ...] = super().process_value(ctx, value)
        if len(vanilla_value) > 1:
            raise click.BadParameter("Cannot apply more than one value", param=self)
        return vanilla_value[0] if vanilla_value else None

    def _throw(self, message: str) -> t.NoReturn:
        raise click.BadParameter(message, param=self)

    def make_metavar(self) -> str:
        """Fixed representation"""
        return f"[{self.NAME}]"


@click.group
@click.option(
    "-l",
    "--log-level",
    help="Logging level. Defaults to ERROR. Also configurable via the CJUNCT_LOG_LEVEL environment variable.",
    type=click.Choice(list(LOG_LEVELS)),
)
@click.option(
    "-d",
    "--display",
    help="Display name. Defaults to prefixes. Also configurable via the CJUNCT_DISPLAY_NAME environment variable.",
    type=click.Choice(list(KNOWN_DISPLAYS)),
)
@cliargs_receiver
def main() -> None:
    """Declarative task runner"""


def load_dotenv() -> None:
    """Try loading environment from the dotenv file.
    Special variable called "HERE" is injected into the environment during dotenv loading,
    which points to the directory of the dotenv file (if not specified in advance)."""
    here_var_name: str = "HERE"
    here_value_was_defined: bool = here_var_name in os.environ
    dotenv_path: Path = C.ENV_FILE
    if not here_value_was_defined:
        os.environ[here_var_name] = str(dotenv_path.parent)
    else:
        logger.debug(f"{here_var_name!r} was set externally")
    try:
        dotenv = DotEnv(dotenv_path=dotenv_path)
        if here_var_name in dotenv.dict():
            logger.debug(f"{here_var_name!r} is explicitly set via dotenv file")
            here_value_was_defined = True
        if dotenv.set_as_environment_variables():
            logger.info(f"Loaded environment variables from {str(dotenv_path)!r}")
        else:
            logger.debug(f"Dotenv not found: {str(dotenv_path)!r}")

    finally:
        if not here_value_was_defined:
            os.environ.pop(here_var_name)


def wrap_cli_command(func):
    """Standard loading and error handling"""

    @main.command
    @cliargs_receiver
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        load_dotenv()
        classlogging.configure_logging(
            level=C.LOG_LEVEL,
            colorize=C.USE_COLOR and not C.LOG_FILE,
            main_file=C.LOG_FILE,
            stream=None if C.LOG_FILE else classlogging.LogStream.STDERR,
        )
        logger.uncork()
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
@click.argument("workflow", cls=WorkflowPositionalArgument)
def run() -> None:
    """Run pipeline immediately."""
    cjunct.Runner().run_sync()


@wrap_cli_command
@click.argument("workflow", cls=WorkflowPositionalArgument)
def validate() -> None:
    """Check workflow validity."""
    action_num: int = len(cjunct.Runner().workflow)
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
