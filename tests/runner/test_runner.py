"""Runner public methods tests"""
# pylint: disable=unused-argument

import typing as t
from pathlib import Path

import pytest

import cjunct
from cjunct.config.loaders import XMLConfigLoader
from cjunct.strategy import BaseStrategy


def test_simple_runner_call(runner_context: None) -> None:
    """Check default call"""
    cjunct.Runner().run_sync()


def test_config_load_success_over_sample(good_xml_config_path: Path) -> None:
    """Check different variations of good configurations"""
    XMLConfigLoader().load(good_xml_config_path)


def test_config_load_failure_over_sample(bad_xml_config: t.Tuple[Path, t.Type[Exception], str]) -> None:
    """Check different variations of bad configurations"""
    config_path, exception, match = bad_xml_config
    with pytest.raises(exception, match=match):
        XMLConfigLoader().load(config_path)


@pytest.mark.parametrize("strategy_class", [cjunct.FreeStrategy, cjunct.SequentialStrategy, cjunct.LooseStrategy])
def test_strategy_runner_call(
    runner_context: None,
    strategy_class: t.Type[BaseStrategy],
    display_collector: t.List[str],
) -> None:
    """Check all strategies"""
    cjunct.Runner(strategy_class=strategy_class).run_sync()
    assert set(display_collector) == {
        '[Foo] | echoing "foo"',
        '[Bar] | echoing "bar"',
    }
