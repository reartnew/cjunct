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

```shell
poetry install --no-root --sync
```

## Running tests

```shell
pytest
```
