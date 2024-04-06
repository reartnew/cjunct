from cjunct.rendering import Lexer


def test_one() -> None:
    assert list(Lexer("@{ a.b.c } @{ a.b.c }")) == [(1, b" a.b.c "), (0, b" "), (1, b" a.b.c ")]


def test_two() -> None:
    assert list(Lexer("""Hello, @{ {"foo": "world"}["foo"] }!""")) == [
        (0, b"Hello, "),
        (1, b' {"foo": "world"}["foo"] '),
        (0, b"!"),
    ]
