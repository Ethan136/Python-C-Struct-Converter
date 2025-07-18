// v5_features_example.h
// 範例：涵蓋 v5 新功能（巢狀 struct/union/array、anonymous bitfield、N-D array、pragma pack）

#pragma pack(push, 1)
struct V5Example {
    struct Nested {
        int x;
        char y;
        union {
            short u1;
            float u2;
        } inner_union;
    } nested;
    int arr2d[2][3]; // N-D array
    union {
        int a;
        struct {
            unsigned int b1 : 3;
            unsigned int   : 2; // anonymous bitfield
            unsigned int b2 : 5;
        } bits;
    } u;
    char tail;
};
#pragma pack(pop) 