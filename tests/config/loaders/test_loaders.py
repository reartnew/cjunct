"""Config loaders public methods tests"""

import typing as t
from pathlib import Path

import pytest

from cjunct.config.loaders import (
    get_default_loader_class_for_file,
    DefaultXMLConfigLoader,
)
from cjunct.config.loaders.base import BaseConfigLoader
from cjunct.exceptions import LoadError


def test_config_load_over_sample(sample_config: t.Tuple[Path, t.Optional[t.Type[Exception]], t.Optional[str]]) -> None:
    """Check different variations of good/bad configurations"""
    config_path, maybe_exception, maybe_match = sample_config
    loader_class: t.Type[BaseConfigLoader] = get_default_loader_class_for_file(config_path)
    # Check good configuration
    if maybe_exception is None:
        loader_class().load(config_path)
        return
    # Check bad configuration
    with pytest.raises(maybe_exception, match=maybe_match):
        loader_class().load(config_path)


def test_loads() -> None:
    """Test normal loading from a string"""
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


def test_loads_bad_structure() -> None:
    """Test bad loading from a string"""
    with pytest.raises(LoadError):
        DefaultXMLConfigLoader().loads(
            """<?xml version="1.0" encoding="UTF-8"?>
    <Actions>
        <Action />
    </Actions>
    """
        )
