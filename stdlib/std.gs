let std = {
  "print": fn(x) {
    __intrinsic_print(x);
    return null;
  },

  "typeof": fn(x): String {
    return __intrinsic_typeof(x);
  },

  "len": fn(x): Int {
    return __intrinsic_len(x);
  }
};

std;
