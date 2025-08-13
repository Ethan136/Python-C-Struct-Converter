#pragma pack(push,1)

// v9 integration example: top-level union preceding a struct, with nested struct and bitfields
union U {
    int a;
    struct {
        unsigned x : 3;     // named bitfield
        unsigned     : 2;   // anonymous bitfield (padding)
        unsigned y : 5;     // named bitfield
    } inner;
};

#pragma pack(pop)

// A separate struct following the union (parser currently returns the first aggregate only)
struct S {
    int z;
};