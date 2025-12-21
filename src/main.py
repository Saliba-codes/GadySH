from __future__ import annotations

import argparse
import sys

from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter
from src.runtime.errors import GadyError


def main() -> int:
    parser = argparse.ArgumentParser(prog="gadysh")
    parser.add_argument("file", nargs="?", help="Path to a .gs file. If omitted, reads stdin.")
    parser.add_argument("--tokens", action="store_true", help="Print tokens and exit.")
    parser.add_argument("--ast", action="store_true", help="Print AST and exit.")
    args = parser.parse_args()

    try:
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                source = f.read()
            filename = args.file
        else:
            source = sys.stdin.read()
            filename = "<stdin>"

        tokens = Lexer(source, filename=filename).tokenize()

        if args.tokens:
            for t in tokens:
                print(t)
            return 0

        program = Parser(tokens, filename=filename).parse_program()

        if args.ast:
            for stmt in program:
                print(stmt)
            return 0

        result = Interpreter().run(program)
        print(result.display())  # host output, not language print
        return 0

    except GadyError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
