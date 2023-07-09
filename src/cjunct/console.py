"""Command-line interface entry"""

import sys
import typing as t

import classlogging
import click

import cjunct
from cjunct.config.constants import C
from cjunct.exceptions import BaseError


class CLIReporter(classlogging.LoggerMixin):
    """Top-level CLI message printer"""

    @classmethod
    def on_error(cls, exception: Exception) -> t.NoReturn:
        """Process an error"""
        log_msg, print_msg, code = (
            ("BaseError", str(exception), exception.CODE)
            if isinstance(exception, BaseError)
            else ("Unhandled exception", f"UNHANDLED EXCEPTION: {exception}", 1)
        )  # type: t.Tuple[str, str, int]
        cls.logger.debug(log_msg, exc_info=True)
        sys.stderr.write(f"! {print_msg.splitlines()[0]}\n")
        sys.exit(code)


@click.group
def main() -> None:
    """Entry group"""


@main.command
def run() -> None:
    """Run pipeline immediately"""
    classlogging.configure_logging(level=C.LOG_LEVEL)
    try:
        cjunct.Runner().run_sync()
    except Exception as e:
        CLIReporter.on_error(e)
