"""Command-line interface entry"""

import sys

import classlogging
import click

import cjunct
from cjunct.config.constants import C
from cjunct.exceptions import BaseError


class Logger(classlogging.LoggerMixin):
    """Top-level CLI logger"""


@click.group
def main() -> None:
    """Entry group"""


@main.command
def run() -> None:
    """Run pipeline immediately"""
    classlogging.configure_logging(level=C.LOG_LEVEL)
    try:
        cjunct.Runner().run_sync()
    except BaseError as e:
        Logger.logger.debug("BaseError", exc_info=True)
        print(e)
        sys.exit(e.CODE)
    except Exception:
        Logger.logger.exception()
        raise
