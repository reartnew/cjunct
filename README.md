# cjunct

Declarative parallel process runner.

## Installation

```shell
pip install cjunct
```

## Usage example

```python
# Put config files into the same directory as this script
import cjunct

if __name__ == "__main__":
    cjunct.Runner().run_sync()
```

## Development environment setup
Requires system-wide poetry>=1.3.2, see [official documentation](https://python-poetry.org).

```shell
poetry install --no-root --sync
```
The root directory for the source code is `src`,
thus one may add it to the project's python path
for better IDE integration.

#### Running tests on current environment

```shell
pytest
```

#### Running tests on all available environments

```shell
tox
```
