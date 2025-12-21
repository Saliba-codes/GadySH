from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class Value:
    def type_name(self) -> str:
        return self.__class__.__name__.replace("Value", "")

    def is_truthy(self) -> bool:
        # Truthiness rule you chose:
        # only false and null are falsey; everything else truthy.
        return True

    def to_python_key(self) -> Any:
        """
        Convert into a Python-hashable key for MapValue.
        Only primitives allowed as keys in v0.1.
        """
        raise TypeError(f"Unhashable key type: {self.type_name()}")

    def __repr__(self) -> str:
        return f"<{self.type_name()}>"

    def display(self) -> str:
        # for host printing/debugging (not a language feature)
        return repr(self)


@dataclass(frozen=True)
class NullValue(Value):
    def is_truthy(self) -> bool:
        return False

    def to_python_key(self) -> Any:
        return ("null",)

    def display(self) -> str:
        return "null"


@dataclass(frozen=True)
class BoolValue(Value):
    value: bool

    def is_truthy(self) -> bool:
        return self.value

    def to_python_key(self) -> Any:
        return ("bool", self.value)

    def display(self) -> str:
        return "true" if self.value else "false"


@dataclass(frozen=True)
class IntValue(Value):
    value: int

    def to_python_key(self) -> Any:
        # unify Int/Float numeric keys by numeric value
        return ("num", float(self.value))

    def display(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class FloatValue(Value):
    value: float

    def to_python_key(self) -> Any:
        return ("num", float(self.value))

    def display(self) -> str:
        # keep a readable float format
        return str(self.value)


@dataclass(frozen=True)
class StringValue(Value):
    value: str

    def to_python_key(self) -> Any:
        return ("str", self.value)

    def display(self) -> str:
        # quotes for clarity
        return f"\"{self.value}\""


@dataclass
class ListValue(Value):
    elements: list[Value]

    def display(self) -> str:
        return "[" + ", ".join(e.display() for e in self.elements) + "]"


@dataclass
class MapValue(Value):
    # key is (tag, python-hashable) as returned by Value.to_python_key()
    items: dict[Any, tuple[Value, Value]]

    def __init__(self) -> None:
        self.items = {}

    def set(self, key: Value, value: Value) -> None:
        k = key.to_python_key()
        self.items[k] = (key, value)

    def get(self, key: Value) -> Value:
        k = key.to_python_key()
        if k not in self.items:
            return NullValue()
        return self.items[k][1]

    def has(self, key: Value) -> bool:
        return key.to_python_key() in self.items

    def display(self) -> str:
        parts = []
        for _k, (orig_key, val) in self.items.items():
            parts.append(f"{orig_key.display()}: {val.display()}")
        return "{ " + ", ".join(parts) + " }"


# handy singletons
NULL = NullValue()
TRUE = BoolValue(True)
FALSE = BoolValue(False)
