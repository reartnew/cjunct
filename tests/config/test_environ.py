"""Environment variables tests"""

import textwrap
import typing as t

import pytest

from cjunct.config.environment import Env
from cjunct.config.loaders.inspect import get_class_annotations


@pytest.mark.parametrize("var", list(get_class_annotations(Env)))
def test_env(var: str) -> None:
    """Test that all vars are described in doc"""
    docs: t.List[str] = textwrap.dedent(Env.__doc__).splitlines()  # type: ignore
    assert any((line.lstrip().startswith(f"{var}: ") for line in docs)), f"Variable {var!r} is not documented"
