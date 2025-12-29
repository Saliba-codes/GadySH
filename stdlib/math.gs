let math = {

  // --- helpers ---
  "_isInt": fn(x): Bool { return std.typeof(x) == "Int"; },
  "_isFloat": fn(x): Bool { return std.typeof(x) == "Float"; },

  // --- basic ---
  "abs": fn(x) {
    if (x < 0) { return 0 - x; }
    return x;
  },

  "min": fn(a, b) {
    if (a < b) { return a; }
    return b;
  },

  "max": fn(a, b) {
    if (a > b) { return a; }
    return b;
  },

  "clamp": fn(x, lo, hi) {
    if (x < lo) { return lo; }
    if (x > hi) { return hi; }
    return x;
  },

  "sign": fn(x): Int {
    if (x < 0) { return -1; }
    if (x > 0) { return 1; }
    return 0;
  },

  // Integer power: exp must be Int >= 0
  "powInt": fn(base, exp: Int) {
    if (exp < 0) { return null; }

    let result = 1;
    let b = base;
    let e: Int = exp;

    while (e > 0) {
      if ((e % 2) == 1) { result = result * b; }
      b = b * b;
      e = std.int(e / 2);
    }

    return result;
  },

  // sqrt using Newton-Raphson
  // returns Float for non-perfect squares; returns Null for x < 0
  "sqrt": fn(x) {
    if (x < 0) { return null; }
    if (x == 0) { return 0.0; }

    let n = std.float(x);
    let guess = n;
    let i: Int = 0;

    while (i < 30) {
      guess = (guess + (n / guess)) / 2.0;
      i = i + 1;
    }

    return guess;
  }
};

math;
