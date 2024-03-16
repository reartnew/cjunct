"""Templar tests"""

import pytest

from cjunct.config.constants import C
from cjunct.exceptions import ActionRenderError
from cjunct.rendering import Templar


def test_outcome_rendering(templar: Templar) -> None:
    """Test outcome rendering"""
    assert templar.render("@{outcomes.Foo.bar}") == "ok"


def test_outcome_unbalanced_expression_rendering(templar: Templar) -> None:
    """Test unbalanced outcome rendering"""
    with pytest.raises(ActionRenderError, match="Outcomes expression has 2 parts of 3"):
        templar.render("@{outcomes.Foo}")


def test_outcome_missing_action_rendering(templar: Templar) -> None:
    """Test missing action outcome rendering"""
    with pytest.raises(ActionRenderError, match="Action not found"):
        templar.render("@{outcomes.'Unknown action'.bar}")


def test_outcome_missing_key_rendering(templar: Templar) -> None:
    """Test missing outcome key rendering"""
    with pytest.raises(ActionRenderError, match="outcome key 'unknown key' not found"):
        templar.render("@{outcomes.Foo.'unknown key'}")


def test_status_rendering(templar: Templar) -> None:
    """Test status rendering"""
    assert templar.render("@{status.Foo}") == "SUCCESS"


def test_status_unbalanced_expression_rendering(templar: Templar) -> None:
    """Test unbalanced status rendering"""
    with pytest.raises(ActionRenderError, match="Status expression has 3 parts of 2"):
        templar.render("@{status.Foo.'extra key'}")


def test_status_missing_action_rendering(templar: Templar) -> None:
    """Test status missing action rendering"""
    with pytest.raises(ActionRenderError, match="Action not found"):
        templar.render("@{status.'Unknown action'}")


def test_environment_rendering(templar: Templar) -> None:
    """Test environment rendering"""
    assert templar.render("@{environment.TEMPLAR_ENVIRONMENT_KEY}") == "test"


def test_environment_unbalanced_expression_rendering(templar: Templar) -> None:
    """Test unbalanced environment rendering"""
    with pytest.raises(ActionRenderError, match="Environment expression has 3 parts of 2"):
        templar.render("@{environment.TEMPLAR_ENVIRONMENT_KEY.'extra key'}")


def test_context_rendering(templar: Templar) -> None:
    """Test context rendering"""
    assert templar.render("@{context.plugh}") == "xyzzy"


def test_context_unbalanced_expression_rendering(templar: Templar) -> None:
    """Test unbalanced context rendering"""
    with pytest.raises(ActionRenderError, match="Context expression has 3 parts of 2"):
        templar.render("@{context.plugh.'extra key'}")


def test_context_missing_key_rendering(templar: Templar) -> None:
    """Test context missing key rendering"""
    with pytest.raises(ActionRenderError, match="Context key not found"):
        templar.render("@{context.'unknown key'}")


def test_unknown_expression_type_rendering(templar: Templar) -> None:
    """Test unknown expression type rendering"""
    with pytest.raises(ActionRenderError, match="Unknown expression type"):
        templar.render("@{'unknown type'.'unknown key'}")


def test_at_sign_escape_rendering(templar: Templar) -> None:
    """Test '@' sign escaping"""
    assert templar.render("@@{outcomes.Foo.bar}") == "@@{outcomes.Foo.bar}"


def test_complex_expression_split_rendering(templar: Templar) -> None:
    """Test complex expression rendering"""
    assert templar.render("@{'outcomes'.'Foo'.'baz qux.fred'}") == "also ok"


def test_expression_cycle_rendering(templar: Templar) -> None:
    """Test outcome rendering"""
    with pytest.raises(ActionRenderError, match="Expression cycle"):
        templar.render("@{context.waldo}")


def test_loose_rendering(templar: Templar, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loose rendering"""
    monkeypatch.setattr(C, "STRICT_OUTCOMES_RENDERING", False)
    assert templar.render("@{outcomes.Foo.'unknown key'}") == ""
