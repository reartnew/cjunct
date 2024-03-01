# cjunct

Declarative parallel process runner.

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cjunct)](https://pypi.python.org/pypi/cjunct/)
[![License](https://img.shields.io/pypi/l/cjunct.svg)](https://pypi.python.org/pypi/cjunct/)
[![PyPI version](https://badge.fury.io/py/cjunct.svg)](https://badge.fury.io/py/cjunct)
![Tests](https://github.com/reartnew/cjunct/workflows/main/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Installation

```shell
pip install cjunct
```

## Usage example

```shell
cjunct run
```

## Development environment setup

Requires system-wide poetry>=1.3.2, see [official documentation](https://python-poetry.org).

```shell
poetry env use python3.8
poetry install --no-root --sync
```

The root directory for the source code is `src`,
thus one may add it to the project's python path
for better IDE integration.

#### Running tests with coverage on current environment

```shell
poetry run pytest --cov --cov-report=html:.coverage_report
```

#### Running tests on all available environments

```shell
poetry run tox
```
