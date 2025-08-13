#pragma pack(push,1)
struct P1 {
    int a;
};

#pragma pack(push,4)
struct P2 {
    int b; \
    int c; // line continuation should merge
};
#pragma pack(pop)

struct P3 {
    union {
        int u1;
        int u2;
    } u;
};
#pragma pack(pop)