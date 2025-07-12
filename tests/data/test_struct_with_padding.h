struct TestStructWithPadding {
    char a;           // 1 byte
    int b;            // 4 bytes (with 3 bytes padding after char a)
    int c;            // 4 bytes
}; 