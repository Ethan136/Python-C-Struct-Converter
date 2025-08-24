// alias_integration.h
// Demonstrates Ux aliases with nested struct/union and bitfields

struct Inner {
    U32 f1 : 3;
    U8  g1 : 1;
};

union UData {
    U16 u;
    U8  arr[2];
};

struct AliasTop {
    struct Inner in;
    union UData u1;
    U64 big;
};
