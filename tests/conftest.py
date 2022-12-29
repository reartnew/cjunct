# pylint: disable=missing-function-docstring

import pytest
import classlogging


@pytest.fixture(autouse=True)
def configure_logging() -> None:
    classlogging.configure_logging(level=classlogging.LogLevel.DEBUG)
