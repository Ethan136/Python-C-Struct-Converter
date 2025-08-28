// v16_referenced_struct_example.h
// 展示：引用型 struct/union、1D/2D 陣列與 forward reference

// 具名 struct 與 union 定義
struct Inner {
    int x;
    char y;
};

union U {
    int a;
    char b;
};

// 引用型 struct/union 的 1D 陣列
struct Outer {
    struct Inner arr[2];
    union U u_arr[2];
    int tail;
};

// 引用型 struct 的 2D 陣列
struct Outer2 {
    struct Inner nd[2][2];
};

// forward reference：先使用後定義
struct UsesForward {
    struct Forward f;
    int z;
};

struct Forward {
    int fx;
};


