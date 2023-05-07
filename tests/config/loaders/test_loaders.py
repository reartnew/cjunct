"""Config loaders public methods tests"""
# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest

from cjunct.config.loaders import XMLConfigLoader


def test_config_load_success_over_sample(good_xml_config_path: Path) -> None:
    """Check different variations of good configurations"""
    XMLConfigLoader().load(good_xml_config_path)


def test_config_load_failure_over_sample(bad_xml_config: t.Tuple[Path, t.Type[Exception], str]) -> None:
    """Check different variations of bad configurations"""
    config_path, exception, match = bad_xml_config
    with pytest.raises(exception, match=match):
        XMLConfigLoader().load(config_path)
