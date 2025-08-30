// v16 example header to validate Import .H behaviors:
// - Multiple top-level struct/union definitions
// - Referenced struct/union types (including arrays)
// - Forward reference within the same header
// - Pointer members should not expand nested

// Top-level union appears before some structs
union UChoice {
    int    a;
    char   b;
};

// Forward reference: Outer references Inner declared later
struct Outer {
    struct Inner ref_single;      // referenced struct
    struct Inner ref_arr1d[2];    // 1D array of referenced struct
    union UChoice u_arr[2];       // union array
    struct Inner *p;              // pointer to struct (should not expand)
};

// The referenced struct, declared after Outer (forward reference target)
struct Inner {
    int  x;
    char y;
};

// Another independent top-level struct
struct Another {
    char flag;
};

