// Example C++ struct definition for testing the parser.
// This struct is designed to have memory padding.

struct PaddedExample {
    char      a;      // 1 byte
    int       b;      // 4 bytes
    char      c;      // 1 byte
    long long d;      // 8 bytes
    bool      e;      // 1 byte
    char*     f;      // 8 bytes (pointer)
};
