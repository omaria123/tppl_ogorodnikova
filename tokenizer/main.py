import sys


class LexicalError(Exception):
    def __init__(self, filename: str, line: int, col: int, message: str):
        super().__init__(f"{filename}:{line}:{col}: lexical: {message}")
        self.filename = filename
        self.line = line
        self.col = col
        self.message = message


class Token:
    def __init__(self, token_type: str, value: str, line: int, col: int):
        self.type = token_type
        self.value = value
        self.line = line
        self.col = col

    def __str__(self):
        return f"({self.type}, {self.value}, {self.line}:{self.col})"

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, {self.line}, {self.col})"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return (
            self.type == other.type
            and self.value == other.value
            and self.line == other.line
            and self.col == other.col
        )


KEYWORDS = {"if", "else", "while", "return", "for", "def"}
SEPARATORS = {"(", ")", "{", "}", ",", ";"}


class Tokenizer:
    def __init__(self, source: str, filename: str = "<stdin>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.length = len(source)
        self.line = 1
        self.col = 1

    def _peek(self, offset: int = 0):
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def _advance(self):
        char = self.source[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char

    def tokenize(self):
        tokens = []

        while self.pos < self.length:
            char = self._peek()

            if char in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            if char == "#":
                while self.pos < self.length and self._peek() not in ("\n", "\r"):
                    self._advance()
                continue

            start_line = self.line
            start_col = self.col

            if char.isalpha() or char == "_":
                tokens.append(self._read_identifier_or_keyword(start_line, start_col))
                continue

            if char.isdigit():
                tokens.append(self._read_number(start_line, start_col))
                continue

            if char == '"':
                tokens.append(self._read_string(start_line, start_col))
                continue

            if char in ("=", "<", ">"):
                if self._peek(1) == "=":
                    op = char + "="
                    self._advance()
                    self._advance()
                    tokens.append(Token("OP", op, start_line, start_col))
                    continue
                self._advance()
                tokens.append(Token("OP", char, start_line, start_col))
                continue

            if char in ("+", "-", "*", "/"):
                self._advance()
                tokens.append(Token("OP", char, start_line, start_col))
                continue

            if char in SEPARATORS:
                self._advance()
                tokens.append(Token("SEP", char, start_line, start_col))
                continue

            self._advance()
            raise LexicalError(
                self.filename, start_line, start_col, f"unexpected character '{char}'"
            )

        return tokens

    def _read_identifier_or_keyword(self, line: int, col: int):
        chars = []
        while self.pos < self.length:
            c = self._peek()
            if c is not None and (c.isalnum() or c == "_"):
                chars.append(self._advance())
            else:
                break
        val = "".join(chars)
        token_type = "KEYWORD" if val in KEYWORDS else "IDENT"
        return Token(token_type, val, line, col)

    def _read_number(self, line: int, col: int):
        chars = []
        while self.pos < self.length:
            c = self._peek()
            if c is not None and c.isdigit():
                chars.append(self._advance())
            else:
                break

        if self._peek() == "." and self._peek(1) is not None and self._peek(1).isdigit():
            chars.append(self._advance())  
            while self.pos < self.length:
                c = self._peek()
                if c is not None and c.isdigit():
                    chars.append(self._advance())
                else:
                    break
            return Token("FLOAT", "".join(chars), line, col)

        return Token("INT", "".join(chars), line, col)

    def _read_string(self, line: int, col: int):
        chars = [self._advance()]  
        while True:
            if self.pos >= self.length:
                raise LexicalError(self.filename, line, col, "unterminated string literal")

            c = self._peek()
            if c in ("\n", "\r"):
                raise LexicalError(self.filename, line, col, "unterminated string literal")

            if c == "\\":
                chars.append(self._advance())  
                if self.pos >= self.length or self._peek() in ("\n", "\r"):
                    raise LexicalError(self.filename, line, col, "unterminated string literal")
                chars.append(self._advance())  
                continue

            if c == '"':
                chars.append(self._advance())  
                break

            chars.append(self._advance())

        return Token("STRING", "".join(chars), line, col)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print("Usage: python main.py <source_file>", file=sys.stderr)
        return 1

    filename = argv[0]
    try:
        with open(filename, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"Error reading file '{filename}': {e}", file=sys.stderr)
        return 1

    tokenizer = Tokenizer(source, filename)
    try:
        tokens = tokenizer.tokenize()
    except LexicalError as err:
        print(err)
        return 1

    for token in tokens:
        print(token)

    return 0


if __name__ == "__main__":
    sys.exit(main())