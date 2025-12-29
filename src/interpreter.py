from __future__ import annotations
from dataclasses import dataclass
import src.ast as ast
from src.runtime.errors import RuntimeError_, TypeError_
from src.runtime.values import (
    Value, NULL, TRUE, FALSE,
    NullValue, BoolValue, IntValue, FloatValue, StringValue,
    ListValue, MapValue,
    NativeFunctionValue
)
from pathlib import Path
from src.lexer import Lexer
from src.parser import Parser

@dataclass
class Environment:
    parent: "Environment | None" = None

    def __post_init__(self) -> None:
        self.values: dict[str, Value] = {}
        self.types: dict[str, str | None] = {}  # store declared type name string for gradual typing

    def define(self, name: str, value: Value, type_name: str | None) -> None:
        self.values[name] = value
        self.types[name] = type_name

    def assign(self, name: str, value: Value) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value)
            return
        raise RuntimeError_(f"Undefined variable '{name}'")

    def get(self, name: str) -> Value:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise RuntimeError_(f"Undefined variable '{name}'")

    def get_declared_type(self, name: str) -> str | None:
        if name in self.types:
            return self.types[name]
        if self.parent is not None:
            return self.parent.get_declared_type(name)
        return None


class ReturnSignal(Exception):
    def __init__(self, value: Value) -> None:
        self.value = value


@dataclass
class FunctionValue(Value):
    name: str
    params: list[tuple[str, str | None]]
    return_type: str | None
    body: ast.Block
    closure: Environment

    def display(self) -> str:
        return f"<fn {self.name}>"


class Interpreter:
    def _get_attr(self, obj: Value, name: str) -> Value:
        # Map attribute access
        if isinstance(obj, MapValue):
            return obj.get(StringValue(name))

        raise RuntimeError_(f"Object of type {obj.type_name()} has no attribute '{name}'")
    
    def __init__(self) -> None:
        self.globals = Environment()
        self.env = self.globals
        self._install_intrinsics()
        self._install_std_from_file()

    def _base_type(self, type_name: str) -> str:
        # "List[Int]" -> "List"
        # "Map[Int, String]" -> "Map"
        return type_name.split("[", 1)[0].strip()

    def _value_type(self, v: Value) -> str:
        # MapValue -> "Map", IntValue -> "Int", etc.
        return v.type_name()

    def _enforce_type(self, expected: str | None, value: Value, where: str) -> None:
        """
        Strict typing:
        - If expected is None: no check (Any)
        - If expected is "Any": no check
        - Otherwise enforce exact base type match.
        """
        if expected is None:
            return
        expected = expected.strip()
        if expected == "Any":
            return

        exp_base = self._base_type(expected)
        got = self._value_type(value)

        if got != exp_base:
            raise TypeError_(f"TypeError: {where}: Expected {expected}, got {got}")

    def _install_intrinsics(self) -> None:
        def _intr_print(args):
            print(args[0].display())
            return NULL

        def _intr_typeof(args):
            return StringValue(args[0].type_name())

        def _intr_len(args):
            v = args[0]
            if isinstance(v, StringValue):
                return IntValue(len(v.value))
            if isinstance(v, ListValue):
                return IntValue(len(v.elements))
            if isinstance(v, MapValue):
                return IntValue(len(v.items))
            raise RuntimeError_("__intrinsic_len expects String, List, or Map")

        self.globals.define("__intrinsic_print", NativeFunctionValue("__intrinsic_print", 1, _intr_print), None)
        self.globals.define("__intrinsic_typeof", NativeFunctionValue("__intrinsic_typeof", 1, _intr_typeof), None)
        self.globals.define("__intrinsic_len", NativeFunctionValue("__intrinsic_len", 1, _intr_len), None)


    def _install_std_from_file(self) -> None:
        # Resolve stdlib path relative to repo root
        # (src/interpreter.py -> src -> repo root)
        repo_root = Path(__file__).resolve().parents[1]
        std_path = repo_root / "stdlib" / "std.gs"

        if not std_path.exists():
            raise RuntimeError_(f"Missing stdlib file: {std_path}")

        source = std_path.read_text(encoding="utf-8")
        tokens = Lexer(source, filename=str(std_path)).tokenize()
        program = Parser(tokens, filename=str(std_path)).parse_program()

        # Run stdlib in the *same interpreter instance* so it can use intrinsics
        result = self.run(program)

        if not isinstance(result, MapValue):
            raise RuntimeError_("stdlib/std.gs must evaluate to a Map (the std module).")

        self.globals.define("std", result, None)

    # -------------------------
    # Program / statements
    # -------------------------
    def run(self, program: list[ast.Stmt]) -> Value:
        last: Value = NULL
        for stmt in program:
            last = self.exec_stmt(stmt)
        return last

    def exec_stmt(self, node: ast.Stmt) -> Value:
        if isinstance(node, ast.ExprStmt):
            return self.eval_expr(node.expr)

        if isinstance(node, ast.VarDecl):
            value = NULL
            if node.initializer is not None:
                value = self.eval_expr(node.initializer)
            self._enforce_type(node.type_name, value, where=f"variable '{node.name}'")
            self.env.define(node.name, value, node.type_name)
            return value

        if isinstance(node, ast.Block):
            return self.exec_block(node)

        if isinstance(node, ast.IfStmt):
            cond = self.eval_expr(node.condition)
            if self._is_truthy(cond):
                return self.exec_stmt(node.then_branch)
            if node.else_branch is not None:
                return self.exec_stmt(node.else_branch)
            return NULL

        if isinstance(node, ast.WhileStmt):
            last: Value = NULL
            while self._is_truthy(self.eval_expr(node.condition)):
                last = self.exec_stmt(node.body)
            return last

        if isinstance(node, ast.ReturnStmt):
            value = NULL
            if node.value is not None:
                value = self.eval_expr(node.value)
            raise ReturnSignal(value)

        if isinstance(node, ast.FunctionDecl):
            fn = FunctionValue(
                name=node.name,
                params=node.params,
                return_type=node.return_type,
                body=node.body,
                closure=self.env,
            )
            self.env.define(node.name, fn, type_name=None)
            return fn

        raise RuntimeError_(f"Unknown statement node: {type(node).__name__}")

    def exec_block(self, block: ast.Block) -> Value:
        previous = self.env
        self.env = Environment(parent=previous)
        try:
            last: Value = NULL
            for stmt in block.statements:
                last = self.exec_stmt(stmt)
            return last
        finally:
            self.env = previous

    # -------------------------
    # Expressions
    # -------------------------
    def eval_expr(self, node: ast.Expr) -> Value:
        if isinstance(node, ast.IntLiteral):
            return IntValue(node.value)

        if isinstance(node, ast.FloatLiteral):
            return FloatValue(node.value)

        if isinstance(node, ast.StringLiteral):
            return StringValue(node.value)

        if isinstance(node, ast.BoolLiteral):
            return TRUE if node.value else FALSE

        if isinstance(node, ast.NullLiteral):
            return NULL

        if isinstance(node, ast.Identifier):
            return self.env.get(node.name)

        if isinstance(node, ast.ListLiteral):
            return ListValue([self.eval_expr(e) for e in node.elements])

        if isinstance(node, ast.MapLiteral):
            m = MapValue()
            for k_expr, v_expr in node.entries:
                k = self.eval_expr(k_expr)
                v = self.eval_expr(v_expr)
                try:
                    m.set(k, v)
                except TypeError as e:
                    raise RuntimeError_(str(e))
            return m

        if isinstance(node, ast.IndexExpr):
            obj = self.eval_expr(node.obj)
            idx = self.eval_expr(node.index)
            return self._index_get(obj, idx)

        if isinstance(node, ast.AssignExpr):
            return self._assign(node)

        if isinstance(node, ast.UnaryExpr):
            right = self.eval_expr(node.expr)
            if node.op == "!":
                return FALSE if self._is_truthy(right) else TRUE
            if node.op == "-":
                return self._negate(right)
            raise RuntimeError_(f"Unknown unary operator {node.op!r}")

        if isinstance(node, ast.BinaryExpr):
            left = self.eval_expr(node.left)

            # short-circuit for && and ||
            if node.op == "&&":
                if not self._is_truthy(left):
                    return left
                return self.eval_expr(node.right)

            if node.op == "||":
                if self._is_truthy(left):
                    return left
                return self.eval_expr(node.right)

            right = self.eval_expr(node.right)
            return self._binary_op(left, node.op, right)

        if isinstance(node, ast.CallExpr):
            callee = self.eval_expr(node.callee)
            args = [self.eval_expr(a) for a in node.args]
            return self._call(callee, args)
        
        if isinstance(node, ast.GetAttrExpr):
            obj = self.eval_expr(node.obj)
            return self._get_attr(obj, node.name)
        
        if isinstance(node, ast.FunctionExpr):
            return FunctionValue(
                name="<anon>",
                params=node.params,
                return_type=node.return_type,
                body=node.body,
                closure=self.env,
            )        

        raise RuntimeError_(f"Unknown expression node: {type(node).__name__}")

    # -------------------------
    # Helpers
    # -------------------------
    def _is_truthy(self, v: Value) -> bool:
        # user-chosen rule: only false and null are falsey
        if isinstance(v, NullValue):
            return False
        if isinstance(v, BoolValue):
            return v.value
        return True

    def _negate(self, v: Value) -> Value:
        if isinstance(v, IntValue):
            return IntValue(-v.value)
        if isinstance(v, FloatValue):
            return FloatValue(-v.value)
        raise RuntimeError_("Unary '-' expects Int or Float")

    def _coerce_number(self, v: Value) -> tuple[str, float | int]:
        if isinstance(v, IntValue):
            return ("int", v.value)
        if isinstance(v, FloatValue):
            return ("float", v.value)
        raise RuntimeError_("Expected a number (Int or Float)")

    def _binary_op(self, a: Value, op: str, b: Value) -> Value:
        # arithmetic
        if op in {"+", "-", "*", "/", "%"}:
            # String concatenation with '+'
            if op == "+" and isinstance(a, StringValue) and isinstance(b, StringValue):
                return StringValue(a.value + b.value)

            # numeric ops
            if isinstance(a, (IntValue, FloatValue)) and isinstance(b, (IntValue, FloatValue)):
                # promote to float if any operand is float
                use_float = isinstance(a, FloatValue) or isinstance(b, FloatValue)

                av = float(a.value) if use_float else int(a.value)
                bv = float(b.value) if use_float else int(b.value)

                if op == "+":
                    return FloatValue(av + bv) if use_float else IntValue(av + bv)
                if op == "-":
                    return FloatValue(av - bv) if use_float else IntValue(av - bv)
                if op == "*":
                    return FloatValue(av * bv) if use_float else IntValue(av * bv)
                if op == "/":
                    if bv == 0:
                        raise RuntimeError_("Division by zero")
                    # division always returns Float (simple and predictable)
                    return FloatValue(float(av) / float(bv))
                if op == "%":
                    if bv == 0:
                        raise RuntimeError_("Modulo by zero")
                    if use_float:
                        raise RuntimeError_("Modulo '%' is only supported for Int in v0.1")
                    return IntValue(int(av) % int(bv))

            raise RuntimeError_(f"Operator {op!r} not supported for these types")

        # comparisons
        if op in {"<", "<=", ">", ">="}:
            if isinstance(a, (IntValue, FloatValue)) and isinstance(b, (IntValue, FloatValue)):
                av = float(a.value)
                bv = float(b.value)
                if op == "<":
                    return TRUE if av < bv else FALSE
                if op == "<=":
                    return TRUE if av <= bv else FALSE
                if op == ">":
                    return TRUE if av > bv else FALSE
                if op == ">=":
                    return TRUE if av >= bv else FALSE
            raise RuntimeError_(f"Operator {op!r} expects numbers")

        if op in {"==", "!="}:
            eq = self._equals(a, b)
            return TRUE if (eq if op == "==" else not eq) else FALSE

        raise RuntimeError_(f"Unknown operator {op!r}")

    def _equals(self, a: Value, b: Value) -> bool:
        # Null
        if isinstance(a, NullValue) and isinstance(b, NullValue):
            return True
        if isinstance(a, NullValue) or isinstance(b, NullValue):
            return False

        # Bool
        if isinstance(a, BoolValue) and isinstance(b, BoolValue):
            return a.value == b.value

        # String
        if isinstance(a, StringValue) and isinstance(b, StringValue):
            return a.value == b.value

        # Numbers (Int/Float cross-compare allowed)
        if isinstance(a, (IntValue, FloatValue)) and isinstance(b, (IntValue, FloatValue)):
            return float(a.value) == float(b.value)

        # Lists/Maps: identity equality in v0.1
        return a is b

    def _index_get(self, obj: Value, idx: Value) -> Value:
        if isinstance(obj, ListValue):
            if not isinstance(idx, IntValue):
                raise RuntimeError_("List index must be Int")
            i = idx.value
            if i < 0 or i >= len(obj.elements):
                return NULL
            return obj.elements[i]

        if isinstance(obj, MapValue):
            try:
                return obj.get(idx)
            except TypeError as e:
                raise RuntimeError_(str(e))

        raise RuntimeError_("Indexing is only supported on List and Map")

    def _index_set(self, obj: Value, idx: Value, value: Value) -> Value:
        if isinstance(obj, ListValue):
            if not isinstance(idx, IntValue):
                raise RuntimeError_("List index must be Int")
            i = idx.value
            if i < 0:
                raise RuntimeError_("Negative list index not supported in v0.1")
            # allow append-like growth by setting exactly at len()
            if i > len(obj.elements):
                raise RuntimeError_("List assignment index out of range")
            if i == len(obj.elements):
                obj.elements.append(value)
            else:
                obj.elements[i] = value
            return value

        if isinstance(obj, MapValue):
            try:
                obj.set(idx, value)
                return value
            except TypeError as e:
                raise RuntimeError_(str(e))

        raise RuntimeError_("Index assignment is only supported on List and Map")

    def _assign(self, node: ast.AssignExpr) -> Value:
        value = self.eval_expr(node.value)

        # identifier assignment
        if isinstance(node.target, ast.Identifier):
            declared = self.env.get_declared_type(node.target.name)
            self._enforce_type(declared, value, where=f"assignment to '{node.target.name}'")
            self.env.assign(node.target.name, value)
            return value

        # index assignment
        if isinstance(node.target, ast.IndexExpr):
            obj = self.eval_expr(node.target.obj)
            idx = self.eval_expr(node.target.index)
            return self._index_set(obj, idx, value)

        raise RuntimeError_("Invalid assignment target")

    def _call(self, callee: Value, args: list[Value]) -> Value:
        # user-defined functions
        if isinstance(callee, FunctionValue):
            if len(args) != len(callee.params):
                raise RuntimeError_(f"{callee.name} expects {len(callee.params)} args, got {len(args)}")

            previous = self.env
            self.env = Environment(parent=callee.closure)
            try:
                for (pname, ptype), arg in zip(callee.params, args):
                    self._enforce_type(ptype, arg, where=f"argument '{pname}' of {callee.name}()")
                    self.env.define(pname, arg, ptype)

                try:
                    self.exec_block(callee.body)
                except ReturnSignal as r:
                    self._enforce_type(callee.return_type, r.value, where=f"return of {callee.name}()")
                    return r.value

                self._enforce_type(callee.return_type, NULL, where=f"return of {callee.name}()")
                return NULL
            finally:
                self.env = previous

        # native (intrinsic) functions
        if isinstance(callee, NativeFunctionValue):
            if callee.arity is not None and len(args) != callee.arity:
                raise RuntimeError_(f"{callee.name} expects {callee.arity} args, got {len(args)}")
            return callee.impl(args)
        raise RuntimeError_("Can only call functions (fn) in v0.1")
    
    def _install_std(self) -> None:
        std = MapValue()

        def _print(args):
            v = args[0]
            print(v.display())
            return NULL

        def _typeof(args):
            return StringValue(args[0].type_name())

        def _len(args):
            v = args[0]
            if isinstance(v, StringValue):
                return IntValue(len(v.value))
            if isinstance(v, ListValue):
                return IntValue(len(v.elements))
            if isinstance(v, MapValue):
                return IntValue(len(v.items))
            raise RuntimeError_("std.len expects String, List, or Map")

        std.set(StringValue("print"), NativeFunctionValue("print", 1, _print))
        std.set(StringValue("typeof"), NativeFunctionValue("typeof", 1, _typeof))
        std.set(StringValue("len"), NativeFunctionValue("len", 1, _len))

        self.globals.define("std", std, None)

