import typing as t

from pytest_data_suites import DataSuite

from cjunct.rendering import Lexer


class LexerTestCase(t.TypedDict):
    source: str
    result: t.List[t.Tuple[int, str]]


class LexerDataSuite(DataSuite):
    plain = LexerTestCase(
        source="foobar",
        result=[(0, "foobar")],
    )
    clean_expression = LexerTestCase(
        source="@{ a.b.c }",
        result=[(1, "a.b.c")],
    )
    multiple_expressions = LexerTestCase(
        source="@{ a.b.c } @{ a.b.c }",
        result=[(1, "a.b.c"), (0, " "), (1, "a.b.c")],
    )
    complex_expression = LexerTestCase(
        source="""Hello, @{ {"foo": "world"}["foo"] }!""",
        result=[(0, "Hello, "), (1, '{"foo":"world"}["foo"]'), (0, "!")],
    )
    expression_with_a_newline = LexerTestCase(
        source="@{a.b.c + \n a.b.d}",
        result=[(1, "a.b.c+a.b.d")],
    )
    shlex_expression = LexerTestCase(
        source='@{ x."y z".w }',
        result=[(1, 'x."y z".w')],
    )
    dashes_expression = LexerTestCase(
        source="@{ x-y.z-w }",
        result=[(1, "x-y.z-w")],
    )
    at_in_the_scalar = LexerTestCase(
        source='"@{ a.b }"',
        result=[(0, '"'), (1, "a.b"), (0, '"')],
    )


@LexerDataSuite.parametrize
def test_lexer(source: str, result: t.List[t.Tuple[int, str]]) -> None:
    assert list(Lexer(source)) == result
