"""Config loaders public methods tests"""
# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest

from cjunct.config.loaders import XMLConfigLoader


def test_config_load_over_sample(xml_config: t.Tuple[Path, t.Optional[t.Type[Exception]], t.Optional[str]]) -> None:
    """Check different variations of good/bad configurations"""
    config_path, maybe_exception, maybe_match = xml_config
    # Check good configuration
    if maybe_exception is None:
        XMLConfigLoader().load(config_path)
        return
    # Check bad configuration
    with pytest.raises(maybe_exception, match=maybe_match):
        XMLConfigLoader().load(config_path)
