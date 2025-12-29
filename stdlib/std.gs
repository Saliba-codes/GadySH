let std = {

  // ---------- Output ----------
  "print": fn(x) {
    __intrinsic_print(x);
    return null;
  },

  // print each arg (variadic style via list for now)
  "printAll": fn(xs: List) {
    let i: Int = 0;
    while (i < std.len(xs)) {
      __intrinsic_print(xs[i]);
      i = i + 1;
    }
    return null;
  },

  // ---------- Introspection ----------
  "typeof": fn(x): String {
    return __intrinsic_typeof(x);
  },

  "len": fn(x): Int {
    return __intrinsic_len(x);
  },

  // ---------- Explicit conversions (strict) ----------
  // Note: These are explicit (allowed) conversions; still no implicit coercion in the language.
  "str": fn(x): String {
    return __intrinsic_str(x);
  },
  
  "int": fn(x): Int {
    return __intrinsic_int(x);
  },

  "float": fn(x): Float {
    return __intrinsic_float(x);
  },

  // ---------- Map helpers ----------
  "has": fn(m: Map, key): Bool {
    return __intrinsic_map_has(m, key);
  },

  "keys": fn(m: Map): List {
    return __intrinsic_map_keys(m);
  },

  "values": fn(m: Map): List {
    return __intrinsic_map_values(m);
  },

  "get": fn(m: Map, key, default) {
    if (std.has(m, key)) {
      return m[key];
    }
    return default;
  }
};

std;
