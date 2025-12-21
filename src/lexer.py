from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.tokens import KEYWORDS, Position, Token, TokenType
from src.runtime.errors import LexError


@dataclass
class Lexer:
    text: str
    filename: str = "<stdin>"

    def __post_init__(self) -> None:
        self.pos = Position(index=-1, line=0, col=-1)
        self.current_char: Optional[str] = None
        self._advance()

    def _advance(self) -> None:
        """Advance by 1 character, updating position."""
        next_index = self.pos.index + 1
        if next_index >= len(self.text):
            # move pos forward once for consistent end positions at EOF
            self.pos = self.pos.advance(self.current_char)
            self.current_char = None
            return

        self.pos = self.pos.advance(self.current_char)
        self.current_char = self.text[next_index]

    def _peek(self) -> Optional[str]:
        i = self.pos.index + 1
        if i >= len(self.text):
            return None
        return self.text[i]

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []

        while self.current_char is not None:
            c = self.current_char

            # whitespace
            if c in " \t\r\n":
                self._advance()
                continue

            # comments
            if c == "/":
                nxt = self._peek()
                if nxt == "/":
                    self._skip_line_comment()
                    continue
                if nxt == "*":
                    self._skip_block_comment()
                    continue
                # otherwise '/' is division
                tokens.append(self._make_simple(TokenType.SLASH))
                continue

            # single-char tokens
            if c == "(":
                tokens.append(self._make_simple(TokenType.LPAREN))
                continue
            if c == ")":
                tokens.append(self._make_simple(TokenType.RPAREN))
                continue
            if c == "{":
                tokens.append(self._make_simple(TokenType.LBRACE))
                continue
            if c == "}":
                tokens.append(self._make_simple(TokenType.RBRACE))
                continue
            if c == "[":
                tokens.append(self._make_simple(TokenType.LBRACKET))
                continue
            if c == "]":
                tokens.append(self._make_simple(TokenType.RBRACKET))
                continue
            if c == ",":
                tokens.append(self._make_simple(TokenType.COMMA))
                continue
            if c == ":":
                tokens.append(self._make_simple(TokenType.COLON))
                continue
            if c == ";":
                tokens.append(self._make_simple(TokenType.SEMI))
                continue
            if c == ".":
                tokens.append(self._make_simple(TokenType.DOT))
                continue
            if c == "+":
                tokens.append(self._make_simple(TokenType.PLUS))
                continue
            if c == "-":
                tokens.append(self._make_simple(TokenType.MINUS))
                continue
            if c == "*":
                tokens.append(self._make_simple(TokenType.STAR))
                continue
            if c == "%":
                tokens.append(self._make_simple(TokenType.PERCENT))
                continue

            # two-char operators (and a few one-char)
            if c == "!":
                start = self.pos
                self._advance()
                if self.current_char == "=":
                    end = self.pos
                    self._advance()
                    tokens.append(Token(TokenType.BANG_EQ, None, start, end))
                else:
                    end = start
                    tokens.append(Token(TokenType.BANG, None, start, end))
                continue

            if c == "=":
                start = self.pos
                self._advance()
                if self.current_char == "=":
                    end = self.pos
                    self._advance()
                    tokens.append(Token(TokenType.EQ_EQ, None, start, end))
                else:
                    end = start
                    tokens.append(Token(TokenType.EQ, None, start, end))
                continue

            if c == "<":
                start = self.pos
                self._advance()
                if self.current_char == "=":
                    end = self.pos
                    self._advance()
                    tokens.append(Token(TokenType.LTE, None, start, end))
                else:
                    end = start
                    tokens.append(Token(TokenType.LT, None, start, end))
                continue

            if c == ">":
                start = self.pos
                self._advance()
                if self.current_char == "=":
                    end = self.pos
                    self._advance()
                    tokens.append(Token(TokenType.GTE, None, start, end))
                else:
                    end = start
                    tokens.append(Token(TokenType.GT, None, start, end))
                continue

            if c == "&":
                start = self.pos
                self._advance()
                if self.current_char == "&":
                    end = self.pos
                    self._advance()
                    tokens.append(Token(TokenType.AND_AND, None, start, end))
                    continue
                raise LexError("Unexpected '&' (did you mean '&&'?)", start, start)

            if c == "|":
                start = self.pos
                self._advance()
                if self.current_char == "|":
                    end = self.pos
                    self._advance()
                    tokens.append(Token(TokenType.OR_OR, None, start, end))
                    continue
                raise LexError("Unexpected '|' (did you mean '||'?)", start, start)

            # literals
            if c.isdigit():
                tokens.append(self._lex_number())
                continue

            if c == '"':
                tokens.append(self._lex_string())
                continue

            # identifiers / keywords
            if c.isalpha() or c == "_":
                tokens.append(self._lex_ident_or_keyword())
                continue

            # unknown
            start = self.pos
            raise LexError(f"Illegal character {c!r}", start, start)

        eof_pos = self.pos
        tokens.append(Token(TokenType.EOF, None, eof_pos, eof_pos))
        return tokens

    def _make_simple(self, ttype: TokenType) -> Token:
        start = self.pos
        end = self.pos
        self._advance()
        return Token(ttype, None, start, end)

    def _skip_line_comment(self) -> None:
        # assumes current_char == '/' and next == '/'
        self._advance()  # '/'
        self._advance()  # second '/'
        while self.current_char is not None and self.current_char != "\n":
            self._advance()
        # consume newline too (optional)
        if self.current_char == "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        # assumes current_char == '/' and next == '*'
        start = self.pos
        self._advance()  # '/'
        self._advance()  # '*'

        while self.current_char is not None:
            if self.current_char == "*" and self._peek() == "/":
                self._advance()  # '*'
                self._advance()  # '/'
                return
            self._advance()

        raise LexError("Unterminated block comment '/* ... */'", start, self.pos)

    def _lex_number(self) -> Token:
        start = self.pos
        num_str = ""
        has_dot = False

        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                if has_dot:
                    break
                has_dot = True
                num_str += "."
                self._advance()
                continue

            num_str += self.current_char
            self._advance()

        end = Position(self.pos.index - 1, self.pos.line, self.pos.col - 1) if num_str else start

        # Edge cases:
        # - "12." is allowed -> float 12.0
        # - ".5" is NOT allowed by this lexer (since we only enter here if first char is digit)
        if has_dot:
            try:
                value = float(num_str)
            except ValueError:
                raise LexError(f"Invalid float literal: {num_str!r}", start, end)
            return Token(TokenType.FLOAT, value, start, end)

        try:
            value = int(num_str)
        except ValueError:
            raise LexError(f"Invalid int literal: {num_str!r}", start, end)
        return Token(TokenType.INT, value, start, end)

    def _lex_string(self) -> Token:
        # current_char == '"'
        start = self.pos
        self._advance()  # consume opening quote

        chars: list[str] = []
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == "\\":
                # escape sequence
                esc_start = self.pos
                self._advance()
                if self.current_char is None:
                    raise LexError("Unterminated string escape", esc_start, self.pos)

                esc = self.current_char
                if esc == "n":
                    chars.append("\n")
                elif esc == "t":
                    chars.append("\t")
                elif esc == "r":
                    chars.append("\r")
                elif esc == '"':
                    chars.append('"')
                elif esc == "\\":
                    chars.append("\\")
                else:
                    raise LexError(f"Unknown escape sequence: \\{esc}", esc_start, self.pos)
                self._advance()
                continue

            # forbid raw newlines inside strings (keeps it simple)
            if self.current_char == "\n":
                raise LexError("Unterminated string literal", start, self.pos)

            chars.append(self.current_char)
            self._advance()

        if self.current_char != '"':
            raise LexError("Unterminated string literal", start, self.pos)

        end_quote_pos = self.pos
        self._advance()  # consume closing quote

        return Token(TokenType.STRING, "".join(chars), start, end_quote_pos)

    def _lex_ident_or_keyword(self) -> Token:
        start = self.pos
        ident = ""

        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == "_"):
            ident += self.current_char
            self._advance()

        # end is last char of ident
        end = Position(self.pos.index - 1, self.pos.line, self.pos.col - 1)

        ttype = KEYWORDS.get(ident, TokenType.IDENT)
        if ttype is TokenType.IDENT:
            return Token(ttype, ident, start, end)
        return Token(ttype, None, start, end)
