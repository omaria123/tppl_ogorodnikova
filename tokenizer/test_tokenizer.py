import pytest
from main import Tokenizer, Token, LexicalError, main


@pytest.fixture
def sample_code():
    return "x = y * 2 + z * 3"


class TestTokenizer:
    def test_prompt_example(self, sample_code):
        t = Tokenizer(sample_code)
        tokens = t.tokenize()
        assert [str(tok) for tok in tokens] == [
            "(IDENT, x, 1:1)",
            "(OP, =, 1:3)",
            "(IDENT, y, 1:5)",
            "(OP, *, 1:7)",
            "(INT, 2, 1:9)",
            "(OP, +, 1:11)",
            "(IDENT, z, 1:13)",
            "(OP, *, 1:15)",
            "(INT, 3, 1:17)",
        ]

    @pytest.mark.parametrize(
        "kw",
        ["if", "else", "while", "return", "for", "def"]
    )
    def test_keywords(self, kw):
        tokens = Tokenizer(kw).tokenize()
        assert len(tokens) == 1
        assert tokens[0] == Token("KEYWORD", kw, 1, 1)

    @pytest.mark.parametrize(
        "ident",
        ["x", "var_1", "_counter", "CamelCase", "for_each"]
    )
    def test_identifiers(self, ident):
        tokens = Tokenizer(ident).tokenize()
        assert len(tokens) == 1
        assert tokens[0] == Token("IDENT", ident, 1, 1)

    @pytest.mark.parametrize(
        "num_str, expected_type",
        [
            ("0", "INT"),
            ("42", "INT"),
            ("100500", "INT"),
            ("3.14", "FLOAT"),
            ("0.001", "FLOAT"),
            ("42.0", "FLOAT"),
        ]
    )
    def test_numbers(self, num_str, expected_type):
        tokens = Tokenizer(num_str).tokenize()
        assert len(tokens) == 1
        assert tokens[0] == Token(expected_type, num_str, 1, 1)

    @pytest.mark.parametrize(
        "op",
        ["+", "-", "*", "/", "=", "==", "<", "<=", ">", ">="]
    )
    def test_operators(self, op):
        tokens = Tokenizer(op).tokenize()
        assert len(tokens) == 1
        assert tokens[0] == Token("OP", op, 1, 1)

    @pytest.mark.parametrize(
        "sep",
        ["(", ")", "{", "}", ",", ";"]
    )
    def test_separators(self, sep):
        tokens = Tokenizer(sep).tokenize()
        assert len(tokens) == 1
        assert tokens[0] == Token("SEP", sep, 1, 1)

    @pytest.mark.parametrize(
        "s",
        ['""', '"hello"', '"with spaces"', '"escaped \\" quote"']
    )
    def test_strings(self, s):
        tokens = Tokenizer(s).tokenize()
        assert len(tokens) == 1
        assert tokens[0] == Token("STRING", s, 1, 1)

    def test_comments_and_whitespace(self):
        code = "# комментарий1\nx = 10\n\t# комментарий2\r\ny = 20"
        tokens = Tokenizer(code).tokenize()
        assert tokens == [
            Token("IDENT", "x", 2, 1),
            Token("OP", "=", 2, 3),
            Token("INT", "10", 2, 5),
            Token("IDENT", "y", 4, 1),
            Token("OP", "=", 4, 3),
            Token("INT", "20", 4, 5),
        ]

    def test_unexpected_char_error(self):
        code = "a @ b"
        t = Tokenizer(code, filename="input.txt")
        with pytest.raises(LexicalError) as exc_info:
            t.tokenize()
        assert str(exc_info.value) == "input.txt:1:3: lexical: unexpected character '@'"

    @pytest.mark.parametrize(
        "bad_code",
        ['"unclosed', '"newline\n"', '"trailing_slash\\']
    )
    def test_unterminated_string_errors(self, bad_code):
        t = Tokenizer(bad_code, filename="test.txt")
        with pytest.raises(LexicalError) as exc_info:
            t.tokenize()
        assert "unterminated string literal" in str(exc_info.value)

    def test_token_equality_and_repr(self):
        t1 = Token("IDENT", "a", 1, 1)
        t2 = Token("IDENT", "a", 1, 1)
        t3 = Token("IDENT", "b", 1, 1)
        assert t1 == t2
        assert t1 != t3
        assert t1 != "not_a_token"
        assert repr(t1) == "Token('IDENT', 'a', 1, 1)"


class TestCLI:
    def test_cli_success(self, tmp_path, capsys):
        test_file = tmp_path / "test.txt"
        test_file.write_text("a = 5", encoding="utf-8")
        code = main([str(test_file)])
        assert code == 0
        captured = capsys.readouterr()
        assert "(IDENT, a, 1:1)" in captured.out

    def test_cli_lexical_error(self, tmp_path, capsys):
        test_file = tmp_path / "test.txt"
        test_file.write_text("a @ b", encoding="utf-8")
        code = main([str(test_file)])
        assert code == 1
        captured = capsys.readouterr()
        assert f"{test_file}:1:3: lexical: unexpected character '@'" in captured.out

    def test_cli_no_args(self, capsys):
        code = main([])
        assert code == 1
        captured = capsys.readouterr()
        assert "Usage:" in captured.err

    def test_cli_file_not_found(self, capsys):
        code = main(["missing_file_404.txt"])
        assert code == 1
        captured = capsys.readouterr()
        assert "Error reading file" in captured.err