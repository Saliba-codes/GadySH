from __future__ import annotations
from dataclasses import dataclass
from src.tokens import Position


@dataclass
class GadyError(Exception):
    message: str
    start: Position | None = None
    end: Position | None = None

    def __str__(self) -> str:
        if self.start is None:
            return self.message
        return f"{self.message} (line {self.start.line+1}, col {self.start.col+1})"


class LexError(GadyError):
    pass


class ParseError(GadyError):
    pass


class RuntimeError_(GadyError):
    pass

class TypeError_(RuntimeError_):
    pass