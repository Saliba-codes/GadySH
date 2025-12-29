# GadySH

GadySH is a general-purpose, interpreted programming language with **strict gradual typing** and a strong emphasis on **clarity, modularity, and language ownership**.

It aims to combine:

- **Python-like** runtime simplicity (interpreted, fast iteration),
- **Java-like** structure (explicit functions, types, and a clear path toward OOP),
- **C++-style maps** (flexible key/value dictionaries with rich indexing semantics).

GadySH runs on the **GadySH VM**, currently implemented in **Python** for simplicity and rapid development.

---

## Status (v0.2)

### Implemented

- Lexer, parser, and AST
- Interpreter (statements, expressions, functions)
- Lists and maps with:
  - indexing
  - indexed assignment
- Strict gradual typing:
  - type annotations enforced at runtime
  - **no implicit type coercion**
  - explicit conversions via standard library
- First-class functions and closures
- Language-level module system:
  - `import "path/to/file.gs"`
  - isolated module environments
  - module caching and circular import detection
- Language-owned standard library (`stdlib/`):
  - `std` module implemented in GadySH
  - minimal host-side intrinsics only
- Standard library features:
  - `std.print(x)`
  - `std.typeof(x)`
  - `std.len(x)`
  - `std.str(x)`
  - `std.int(x)`
  - `std.float(x)`
  - `std.has(map, key)`
  - `std.get(map, key, default)`
  - `std.keys(map)`
  - `std.values(map)`
- Math module (`stdlib/math.gs`):
  - `abs`, `min`, `max`, `clamp`, `sign`
  - `sqrt` (Newton method)
  - `powInt` (integer exponentiation)

---

## Notes

- `print` is **not** a language keyword; output is provided via `std.print`.
- The standard library is intentionally **language-owned**, written in GadySH itself.
- The host VM exposes only a small set of **intrinsics** for I/O and reflection.

---

## Quick Start

Run from the repository root:

```bash
python -m src.main
```
Example:

```GadySH
let math = import "stdlib/math.gs";
std.print(math.sqrt(2));
std.print(math.powInt(2, 10));
```
