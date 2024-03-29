"""Config loaders public methods tests"""

import typing as t
from pathlib import Path

import pytest

from cjunct.config.loaders.base import AbstractBaseConfigLoader
from cjunct.config.loaders.default.yaml import DefaultYAMLConfigLoader
from cjunct.config.loaders.helpers import get_default_loader_class_for_source
from cjunct.exceptions import LoadError


def test_config_load_over_sample(sample_config: t.Tuple[Path, t.Optional[t.Type[Exception]], t.Optional[str]]) -> None:
    """Check different variations of good/bad configurations"""
    config_path, maybe_exception, maybe_match = sample_config
    loader_class: t.Type[AbstractBaseConfigLoader] = get_default_loader_class_for_source(config_path)
    # Check good configuration
    if maybe_exception is None:
        loader_class().load(config_path)
        return
    # Check bad configuration
    with pytest.raises(maybe_exception, match=maybe_match):
        loader_class().load(config_path)


def test_yaml_loads() -> None:
    """Test normal YAML loading from a string"""
    DefaultYAMLConfigLoader().loads(
        """---
actions:
  - name: RunAnsible
    type: shell
    description: Run ansible
    command: playbooks/Dummy.yml
"""
    )


def test_yaml_loads_bad_structure() -> None:
    """Test bad YAML loading from a string"""
    with pytest.raises(LoadError):
        DefaultYAMLConfigLoader().loads(
            """---
actions:
  - {}
"""
        )
