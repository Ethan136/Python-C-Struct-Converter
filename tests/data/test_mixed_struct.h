struct TestMixedStruct {
    char a;           // 1 byte
    short b;          // 2 bytes (with 1 byte padding after char a)
    int c;            // 4 bytes
    long long d;      // 8 bytes
}; 