# GadySH

GadySH is an object-oriented, general-purpose, gradually typed programming language.

It aims to combine:

- **Python-like** runtime simplicity (interpreted, fast iteration),
- **Java-like** structure (clear syntax and a path toward OOP),
- and **C++-style maps** (flexible key/value dictionaries).

GadySH runs on the **GadySH VM**, currently implemented in **Python** for simplicity and rapid development.

## Status (v0.1)

Implemented:

- Lexer + parser + AST
- Interpreter (statements, expressions, functions)
- Lists and maps with indexing + indexed assignment
- Strict gradual typing (type annotations enforced at runtime; no implicit coercion)
- `std` module with dot access:
  - `std.print(x)`
  - `std.typeof(x)`
  - `std.len(x)`

Notes:

- `print` is **not** a language keyword; output is provided via `std.print`.
- The standard library is designed to become **language-owned** later (implemented in GadySH), with a minimal intrinsic surface in the VM.

## Quick Start

Run from the repository root:

```bash
python -m src.main
```
