from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


@dataclass(frozen=True)
class Position:
    """A simple source position for good error messages."""
    index: int
    line: int
    col: int

    def advance(self, current_char: str | None) -> "Position":
        if current_char == "\n":
            return Position(self.index + 1, self.line + 1, 0)
        return Position(self.index + 1, self.line, self.col + 1)


class TokenType(Enum):
    # single-char
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    COMMA = auto()       # ,
    COLON = auto()       # :
    SEMI = auto()        # ;
    DOT = auto()         # .

    # one/two-char operators
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    PERCENT = auto()     # %

    BANG = auto()        # !
    BANG_EQ = auto()     # !=
    EQ = auto()          # =
    EQ_EQ = auto()       # ==
    LT = auto()          # <
    LTE = auto()         # <=
    GT = auto()          # >
    GTE = auto()         # >=

    AND_AND = auto()     # &&
    OR_OR = auto()       # ||

    # literals/ident
    IDENT = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()

    # keywords
    IMPORT = auto()
    LET = auto()
    FN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "import": TokenType.IMPORT,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: Any
    start: Position
    end: Position

    def __repr__(self) -> str:
        if self.value is None:
            return f"{self.type.name}"
        return f"{self.type.name}({self.value!r})"
