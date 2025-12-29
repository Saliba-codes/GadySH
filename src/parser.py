from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.tokens import Token, TokenType
from src.runtime.errors import ParseError
import src.ast as ast


@dataclass
class Parser:
    tokens: list[Token]
    filename: str = "<stdin>"

    def __post_init__(self) -> None:
        self.i = 0

    # -------------------------
    # Core navigation
    # -------------------------
    def current(self) -> Token:
        return self.tokens[self.i]

    def previous(self) -> Token:
        return self.tokens[self.i - 1]

    def at_end(self) -> bool:
        return self.current().type == TokenType.EOF

    def advance(self) -> Token:
        if not self.at_end():
            self.i += 1
        return self.previous()

    def check(self, t: TokenType) -> bool:
        return self.current().type == t

    def match(self, *types: TokenType) -> bool:
        if self.current().type in types:
            self.advance()
            return True
        return False

    def expect(self, t: TokenType, msg: str) -> Token:
        if self.check(t):
            return self.advance()
        tok = self.current()
        raise ParseError(msg, tok.start, tok.end)

    # -------------------------
    # Entry points
    # -------------------------
    def parse_program(self) -> list[ast.Stmt]:
        stmts: list[ast.Stmt] = []
        while not self.at_end():
            stmts.append(self.parse_statement())
        return stmts

    # -------------------------
    # Statements
    # -------------------------
    def parse_statement(self) -> ast.Stmt:
        if self.match(TokenType.LET):
            return self.parse_var_decl()
        if self.match(TokenType.FN):
            return self.parse_fn_decl()
        if self.match(TokenType.IF):
            return self.parse_if()
        if self.match(TokenType.WHILE):
            return self.parse_while()
        if self.match(TokenType.RETURN):
            return self.parse_return()
        if self.match(TokenType.LBRACE):
            return self.parse_block_opened()

        # expression statement
        expr = self.parse_expression()
        self.expect(TokenType.SEMI, "Expected ';' after expression.")
        return ast.ExprStmt(expr)

    def parse_block_opened(self) -> ast.Block:
        # '{' already consumed
        stmts: list[ast.Stmt] = []
        while not self.check(TokenType.RBRACE) and not self.at_end():
            stmts.append(self.parse_statement())
        self.expect(TokenType.RBRACE, "Expected '}' after block.")
        return ast.Block(stmts)

    def parse_var_decl(self) -> ast.VarDecl:
        name_tok = self.expect(TokenType.IDENT, "Expected identifier after 'let'.")
        type_name: Optional[str] = None
        initializer: Optional[ast.Expr] = None

        if self.match(TokenType.COLON):
            type_name = self.parse_type_name()

        if self.match(TokenType.EQ):
            initializer = self.parse_expression()

        self.expect(TokenType.SEMI, "Expected ';' after variable declaration.")
        return ast.VarDecl(name=name_tok.value, type_name=type_name, initializer=initializer)

    def parse_fn_decl(self) -> ast.FunctionDecl:
        name_tok = self.expect(TokenType.IDENT, "Expected function name after 'fn'.")
        self.expect(TokenType.LPAREN, "Expected '(' after function name.")

        params: list[tuple[str, Optional[str]]] = []
        if not self.check(TokenType.RPAREN):
            while True:
                p_name = self.expect(TokenType.IDENT, "Expected parameter name.").value
                p_type: Optional[str] = None
                if self.match(TokenType.COLON):
                    p_type = self.parse_type_name()
                params.append((p_name, p_type))
                if not self.match(TokenType.COMMA):
                    break

        self.expect(TokenType.RPAREN, "Expected ')' after parameters.")

        return_type: Optional[str] = None
        if self.match(TokenType.COLON):
            return_type = self.parse_type_name()

        self.expect(TokenType.LBRACE, "Expected '{' before function body.")
        body = self.parse_block_opened()

        return ast.FunctionDecl(
            name=name_tok.value,
            params=params,
            return_type=return_type,
            body=body,
        )

    def parse_if(self) -> ast.IfStmt:
        self.expect(TokenType.LPAREN, "Expected '(' after 'if'.")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after if condition.")
        then_branch = self.parse_statement()

        else_branch: Optional[ast.Stmt] = None
        if self.match(TokenType.ELSE):
            else_branch = self.parse_statement()

        return ast.IfStmt(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def parse_while(self) -> ast.WhileStmt:
        self.expect(TokenType.LPAREN, "Expected '(' after 'while'.")
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN, "Expected ')' after while condition.")
        body = self.parse_statement()
        return ast.WhileStmt(condition=condition, body=body)

    def parse_return(self) -> ast.ReturnStmt:
        if self.check(TokenType.SEMI):
            self.advance()
            return ast.ReturnStmt(value=None)

        value = self.parse_expression()
        self.expect(TokenType.SEMI, "Expected ';' after return value.")
        return ast.ReturnStmt(value=value)

    # -------------------------
    # Types (v0.1: store as string)
    # -------------------------
    def parse_type_name(self) -> str:
        """
        Accepts:
          Int
          Float
          Map[Int, String]
          List[Int]
        We store it as a raw string for now (runtime typing comes later).
        """
        base = self.expect(TokenType.IDENT, "Expected type name after ':'.").value
        s = base

        if self.match(TokenType.LBRACKET):
            parts = ["["]
            depth = 1
            while depth > 0 and not self.at_end():
                if self.match(TokenType.LBRACKET):
                    depth += 1
                    parts.append("[")
                    continue
                if self.match(TokenType.RBRACKET):
                    depth -= 1
                    parts.append("]")
                    continue
                if self.match(TokenType.COMMA):
                    parts.append(",")
                    continue

                # inside type args we allow identifiers
                if self.match(TokenType.IDENT):
                    parts.append(self.previous().value)
                    continue

                tok = self.current()
                raise ParseError("Invalid token in type annotation.", tok.start, tok.end)

            if depth != 0:
                tok = self.current()
                raise ParseError("Unterminated type annotation (missing ']').", tok.start, tok.end)

            s += "".join(parts)

        return s

    # -------------------------
    # Expressions
    # -------------------------
    def parse_expression(self) -> ast.Expr:
        return self.parse_assignment()

    def parse_assignment(self) -> ast.Expr:
        expr = self.parse_or()

        if self.match(TokenType.EQ):
            eq_tok = self.previous()
            value = self.parse_assignment()  # right-associative

            if isinstance(expr, ast.Identifier) or isinstance(expr, ast.IndexExpr):
                return ast.AssignExpr(target=expr, value=value)

            raise ParseError("Invalid assignment target.", eq_tok.start, eq_tok.end)

        return expr

    def parse_or(self) -> ast.Expr:
        expr = self.parse_and()
        while self.match(TokenType.OR_OR):
            op = "||"
            right = self.parse_and()
            expr = ast.BinaryExpr(expr, op, right)
        return expr

    def parse_and(self) -> ast.Expr:
        expr = self.parse_equality()
        while self.match(TokenType.AND_AND):
            op = "&&"
            right = self.parse_equality()
            expr = ast.BinaryExpr(expr, op, right)
        return expr

    def parse_equality(self) -> ast.Expr:
        expr = self.parse_compare()
        while self.match(TokenType.EQ_EQ, TokenType.BANG_EQ):
            op = "==" if self.previous().type == TokenType.EQ_EQ else "!="
            right = self.parse_compare()
            expr = ast.BinaryExpr(expr, op, right)
        return expr

    def parse_compare(self) -> ast.Expr:
        expr = self.parse_term()
        while self.match(TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            t = self.previous().type
            op = {TokenType.LT: "<", TokenType.LTE: "<=", TokenType.GT: ">", TokenType.GTE: ">="}[t]
            right = self.parse_term()
            expr = ast.BinaryExpr(expr, op, right)
        return expr

    def parse_term(self) -> ast.Expr:
        expr = self.parse_factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = "+" if self.previous().type == TokenType.PLUS else "-"
            right = self.parse_factor()
            expr = ast.BinaryExpr(expr, op, right)
        return expr

    def parse_factor(self) -> ast.Expr:
        expr = self.parse_unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            t = self.previous().type
            op = {TokenType.STAR: "*", TokenType.SLASH: "/", TokenType.PERCENT: "%"}[t]
            right = self.parse_unary()
            expr = ast.BinaryExpr(expr, op, right)
        return expr

    def parse_unary(self) -> ast.Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            op = "!" if self.previous().type == TokenType.BANG else "-"
            right = self.parse_unary()
            return ast.UnaryExpr(op, right)
        return self.parse_call()

    def parse_call(self) -> ast.Expr:
        expr = self.parse_primary()

        while True:
            # attribute access: obj.name
            if self.match(TokenType.DOT):
                name_tok = self.expect(TokenType.IDENT, "Expected identifier after '.'.")
                expr = ast.GetAttrExpr(expr, name_tok.value)
                continue  # <-- CRITICAL

            # function call: (args?)
            if self.match(TokenType.LPAREN):
                args: list[ast.Expr] = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        args.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.expect(TokenType.RPAREN, "Expected ')' after arguments.")
                expr = ast.CallExpr(expr, args)
                continue

            # indexing: [expr]
            if self.match(TokenType.LBRACKET):
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET, "Expected ']' after index.")
                expr = ast.IndexExpr(expr, index)
                continue

            break

        return expr


    def parse_primary(self) -> ast.Expr:
        if self.match(TokenType.INT):
            return ast.IntLiteral(self.previous().value)
        if self.match(TokenType.FLOAT):
            return ast.FloatLiteral(self.previous().value)
        if self.match(TokenType.STRING):
            return ast.StringLiteral(self.previous().value)
        if self.match(TokenType.TRUE):
            return ast.BoolLiteral(True)
        if self.match(TokenType.FALSE):
            return ast.BoolLiteral(False)
        if self.match(TokenType.NULL):
            return ast.NullLiteral()

                # function expression (anonymous)
        if self.match(TokenType.FN):
            self.expect(TokenType.LPAREN, "Expected '(' after 'fn'.")
            params: list[tuple[str, Optional[str]]] = []

            if not self.check(TokenType.RPAREN):
                while True:
                    p_name = self.expect(TokenType.IDENT, "Expected parameter name.").value
                    p_type: Optional[str] = None
                    if self.match(TokenType.COLON):
                        p_type = self.parse_type_name()
                    params.append((p_name, p_type))
                    if not self.match(TokenType.COMMA):
                        break

            self.expect(TokenType.RPAREN, "Expected ')' after parameters.")

            return_type: Optional[str] = None
            if self.match(TokenType.COLON):
                return_type = self.parse_type_name()

            self.expect(TokenType.LBRACE, "Expected '{' before function body.")
            body = self.parse_block_opened()

            return ast.FunctionExpr(params=params, return_type=return_type, body=body)

        if self.match(TokenType.IDENT):
            return ast.Identifier(self.previous().value)

        # list literal
        if self.match(TokenType.LBRACKET):
            elems: list[ast.Expr] = []
            if not self.check(TokenType.RBRACKET):
                while True:
                    elems.append(self.parse_expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RBRACKET, "Expected ']' after list literal.")
            return ast.ListLiteral(elems)

        # map literal
        if self.match(TokenType.LBRACE):
            entries: list[tuple[ast.Expr, ast.Expr]] = []
            if not self.check(TokenType.RBRACE):
                while True:
                    key = self.parse_expression()
                    self.expect(TokenType.COLON, "Expected ':' after map key.")
                    val = self.parse_expression()
                    entries.append((key, val))
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RBRACE, "Expected '}' after map literal.")
            return ast.MapLiteral(entries)

        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        tok = self.current()
        raise ParseError("Expected expression.", tok.start, tok.end)
