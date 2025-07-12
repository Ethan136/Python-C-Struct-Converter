// Example C++ struct definition for testing the parser.
// This struct is designed to have memory padding and bit fields.

struct CombinedExample {
    char      a;      // 1 byte
    int       b;      // 4 bytes
    int       c1 : 1; // bit field (1 bit)
    int       c2 : 2; // bit field (2 bits)
    int       c3 : 5; // bit field (5 bits)
    char      d;      // 1 byte
    long long e;      // 8 bytes
    unsigned char f;  // 1 byte (was bool)
    char*     g;      // 8 bytes (pointer)
};
