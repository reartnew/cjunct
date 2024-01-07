"""Config loaders public methods tests"""

import typing as t
from pathlib import Path

import pytest

from cjunct.config.loaders.base import AbstractBaseConfigLoader
from cjunct.config.loaders.default.xml import DefaultXMLConfigLoader
from cjunct.config.loaders.default.yaml import DefaultYAMLConfigLoader
from cjunct.config.loaders.helpers import get_default_loader_class_for_file
from cjunct.exceptions import LoadError


def test_config_load_over_sample(sample_config: t.Tuple[Path, t.Optional[t.Type[Exception]], t.Optional[str]]) -> None:
    """Check different variations of good/bad configurations"""
    config_path, maybe_exception, maybe_match = sample_config
    loader_class: t.Type[AbstractBaseConfigLoader] = get_default_loader_class_for_file(config_path)
    # Check good configuration
    if maybe_exception is None:
        loader_class().load(config_path)
        return
    # Check bad configuration
    with pytest.raises(maybe_exception, match=maybe_match):
        loader_class().load(config_path)


def test_xml_loads() -> None:
    """Test normal XML loading from a string"""
    DefaultXMLConfigLoader().loads(
        """<?xml version="1.0" encoding="UTF-8"?>
<Actions>
    <Action name="RunAnsible">
        <description>Run ansible</description>
        <type>shell</type>
        <command>playbooks/Dummy.yml</command>
    </Action>
</Actions>
"""
    )


def test_xml_loads_bad_structure() -> None:
    """Test bad XML loading from a string"""
    with pytest.raises(LoadError):
        DefaultXMLConfigLoader().loads(
            """<?xml version="1.0" encoding="UTF-8"?>
    <Actions>
        <Action />
    </Actions>
    """
        )


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
