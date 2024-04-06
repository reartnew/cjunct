from cjunct.rendering import Lexer


def test_one() -> None:
    assert list(Lexer("@{ a.b.c } @{ a.b.c }")) == [(1, "a .b .c "), (0, " "), (1, "a .b .c ")]


def test_two() -> None:
    assert list(Lexer("""Hello, @{ {"foo": "world"}["foo"] }!""")) == [
        (0, "Hello, "),
        (1, '{"foo":"world"}["foo"]'),
        (0, "!"),
    ]


def test_three() -> None:
    assert list(Lexer("@{ a.b.c + \n a.b.d }")) == [(1, "a .b .c +a .b .d ")]
