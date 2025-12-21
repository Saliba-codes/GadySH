from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional


# ===== Base nodes =====

class ASTNode:
    pass


class Expr(ASTNode):
    pass


class Stmt(ASTNode):
    pass


# ===== Expressions =====

@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class FloatLiteral(Expr):
    value: float


@dataclass
class StringLiteral(Expr):
    value: str


@dataclass
class BoolLiteral(Expr):
    value: bool


@dataclass
class NullLiteral(Expr):
    pass


@dataclass
class Identifier(Expr):
    name: str


@dataclass
class UnaryExpr(Expr):
    op: str
    expr: Expr


@dataclass
class BinaryExpr(Expr):
    left: Expr
    op: str
    right: Expr


@dataclass
class AssignExpr(Expr):
    target: Expr
    value: Expr


@dataclass
class CallExpr(Expr):
    callee: Expr
    args: List[Expr]


@dataclass
class IndexExpr(Expr):
    obj: Expr
    index: Expr


@dataclass
class ListLiteral(Expr):
    elements: List[Expr]


@dataclass
class MapLiteral(Expr):
    entries: List[tuple[Expr, Expr]]


# ===== Statements =====

@dataclass
class ExprStmt(Stmt):
    expr: Expr


@dataclass
class VarDecl(Stmt):
    name: str
    type_name: Optional[str]
    initializer: Optional[Expr]


@dataclass
class Block(Stmt):
    statements: List[Stmt]


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: Stmt


@dataclass
class ReturnStmt(Stmt):
    value: Optional[Expr]


@dataclass
class FunctionDecl(Stmt):
    name: str
    params: List[tuple[str, Optional[str]]]
    return_type: Optional[str]
    body: Block
