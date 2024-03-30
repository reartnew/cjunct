# cjunct

Cjunct (pronounced *SEE-jen*) is an extensible declarative task runner,
aimed to make complex routine jobs easier to configure.

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cjunct)](https://pypi.python.org/pypi/cjunct/)
[![License](https://img.shields.io/pypi/l/cjunct.svg)](https://opensource.org/license/mit/)
[![PyPI version](https://badge.fury.io/py/cjunct.svg)](https://pypi.python.org/pypi/cjunct/)
[![Tests](https://github.com/reartnew/cjunct/workflows/main/badge.svg)](https://github.com/reartnew/cjunct/actions/workflows/main.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

<details>
  <summary>Table of Contents</summary>

1. [Installation](#installation)
2. [Usage](#usage)
3. [How to contribute](#contribute)

</details>

<div id="installation"></div>

## Installation

```shell
# Install only core components
pip install cjunct

# Install both core components and docker-related extensions
pip install "cjunct[docker]"
```

<div id="usage"></div>

## Usage

#### Basic examples

```shell
# Execute a workflow that is outlined
# in the workdir-located cjunct.yaml file
cjunct run

# Print usage
cjunct --help
```

Options are configured either via environment variables or via command-line switches. The most common are:

- `CJUNCT_LOG_LEVEL`: Set log level.
- `CJUNCT_LOG_FILE`: Set log file.
- `CJUNCT_WORKFLOW_FILE`: Set the workflow file path explicitly.
- `CJUNCT_STRATEGY_NAME`: Manage execution strategy.
- `CJUNCT_ACTIONS_CLASS_DEFINITIONS_DIRECTORY`: Where to look for custom action runners.
- `CJUNCT_STRICT_OUTCOMES_RENDERING`: Manage failure behaviour when an outcome key is missing.

Full list of used environment variable names can be obtained with this command:

```shell
cjunct info env-vars
```

<div id="contribute"></div>

## How to contribute

#### Development environment setup

Requires system-wide poetry>=1.3.2, see [official documentation](https://python-poetry.org).

```shell
poetry env use python3.8
poetry install --no-root --sync --all-extras
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
