// v5_features_example.h
// 範例：涵蓋 v5 新功能（巢狀 struct/union/array、anonymous bitfield、N-D array、pragma pack）

#pragma pack(push, 1)
struct V5Example {
    struct Nested {
        U32 x;
        U8 y;
        union {
            U16 u1;
            U32 *pu2;
        } inner_union;
    } nested;
    U8* arr2d[2][3]; // N-D array
    union {
        U32 a;
        struct {
            unsigned int b1 : 3;
            unsigned int   : 2; // anonymous bitfield
            unsigned int b2 : 5;
        } bits;
    } u;
    U8 tail;
};
#pragma pack(pop) 