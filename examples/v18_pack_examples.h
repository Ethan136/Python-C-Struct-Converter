#pragma pack(push,1)
struct Pack1_Simple {
    char c;
    int i;
};
#pragma pack(pop)

#pragma pack(2)
struct Pack2_Array {
    short s;
    int arr[2];
};

#pragma pack(1)
struct Pack1_Bitfields {
    unsigned int a:3;
    unsigned int b:5;
    unsigned int c:8;
};

#pragma pack(1)
struct Pack1_NestedUnion {
    union {
        int x;
        char y[4];
    } u;
    char t;
};
