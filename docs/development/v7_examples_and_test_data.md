# v7 範例與測試資料（Deprecated）

> Note (V23): 本文件為歷史說明，範例仍可參考。系統現已移除 v7/legacy 切換，Modern 為唯一介面。請參閱：
> - `docs/development/V23_MIGRATION_GUIDE.md`
> - `src/view/README.md`（現況 GUI 行為）

## 1. 複雜結構範例

### 1.1 基本巢狀結構範例
```c
// 基本巢狀 struct 範例
struct BasicNested {
    struct Inner {
        int x;
        char y;
        float z;
    } inner;
    int outer_value;
    char outer_char;
};
```

### 1.2 複雜巢狀結構範例
```c
// 複雜巢狀結構，包含 struct、union、array、bitfield
struct ComplexNested {
    // 巢狀 struct
    struct Point {
        int x;
        int y;
    } point;
    
    // 巢狀 union
    union Data {
        int integer;
        float floating;
        struct {
            unsigned int low : 16;
            unsigned int high : 16;
        } split;
    } data;
    
    // 巢狀陣列
    struct Matrix {
        float values[3][3];
    } matrix;
    
    // 位元欄位
    struct Flags {
        unsigned int flag1 : 1;
        unsigned int flag2 : 1;
        unsigned int : 6;  // 匿名位元欄位
        unsigned int mode : 4;
    } flags;
    
    // 混合結構
    union Mixed {
        struct {
            char name[32];
            int id;
        } named;
        struct {
            unsigned int code : 8;
            unsigned int : 8;
            unsigned int value : 16;
        } coded;
    } mixed;
    
    // 多維陣列
    int grid[2][3][4];
    
    // 巢狀結構陣列
    struct Item {
        char name[16];
        int count;
        float price;
    } items[5];
};
```

### 1.3 極端複雜結構範例
```c
// 極端複雜的巢狀結構，用於壓力測試
struct ExtremeComplex {
    // 深度巢狀
    struct Level1 {
        struct Level2 {
            struct Level3 {
                struct Level4 {
                    struct Level5 {
                        int deepest_value;
                        char deepest_char;
                    } level5;
                    float level4_float;
                } level4;
                double level3_double;
            } level3;
            long level2_long;
        } level2;
        short level1_short;
    } level1;
    
    // 大型陣列
    struct LargeArray {
        int data[10][10][10];  // 1000 個元素
    } large_array;
    
    // 複雜位元欄位組合
    struct ComplexBitfields {
        unsigned int a : 1;
        unsigned int b : 2;
        unsigned int c : 3;
        unsigned int : 2;
        unsigned int d : 4;
        unsigned int e : 5;
        unsigned int f : 6;
        unsigned int g : 7;
    } complex_bits;
    
    // 匿名結構和聯合
    struct {
        int anonymous_int;
        char anonymous_char;
        union {
            float u_float;
            struct {
                unsigned int u_low : 16;
                unsigned int u_high : 16;
            } u_split;
        } anonymous_union;
    } anonymous_struct;
    
    // 混合巢狀陣列
    struct MixedArray {
        struct {
            int x;
            char y;
        } simple[3];
        union {
            int i;
            float f;
        } mixed[2];
    } mixed_array;
};
```

## 2. XML 測試資料格式

### 2.1 基本 XML 測試資料結構
```xml
<?xml version="1.0" encoding="UTF-8"?>
<v7_test_suite>
    <test_case name="basic_nested_struct">
        <description>基本巢狀結構測試</description>
        <input>
            <![CDATA[
            struct BasicNested {
                struct Inner {
                    int x;
                    char y;
                    float z;
                } inner;
                int outer_value;
                char outer_char;
            };
            ]]>
        </input>
        <expected_ast>
            <node type="struct" name="BasicNested">
                <children>
                    <node type="struct" name="inner">
                        <children>
                            <node type="int" name="x"/>
                            <node type="char" name="y"/>
                            <node type="float" name="z"/>
                        </children>
                    </node>
                    <node type="int" name="outer_value"/>
                    <node type="char" name="outer_char"/>
                </children>
            </node>
        </expected_ast>
        <expected_flattened>
            <node name="inner.x" type="int" offset="0" size="4"/>
            <node name="inner.y" type="char" offset="4" size="1"/>
            <node name="inner.z" type="float" offset="8" size="4"/>
            <node name="outer_value" type="int" offset="12" size="4"/>
            <node name="outer_char" type="char" offset="16" size="1"/>
        </expected_flattened>
        <expected_layout>
            <total_size>20</total_size>
            <alignment>4</alignment>
        </expected_layout>
    </test_case>
</v7_test_suite>
```

### 2.2 複雜結構 XML 測試資料
```xml
<test_case name="complex_nested_structure">
    <description>複雜巢狀結構測試</description>
    <input>
        <![CDATA[
        struct ComplexNested {
            struct Point {
                int x;
                int y;
            } point;
            union Data {
                int integer;
                float floating;
                struct {
                    unsigned int low : 16;
                    unsigned int high : 16;
                } split;
            } data;
            struct Matrix {
                float values[3][3];
            } matrix;
            struct Flags {
                unsigned int flag1 : 1;
                unsigned int flag2 : 1;
                unsigned int : 6;
                unsigned int mode : 4;
            } flags;
        };
        ]]>
    </input>
    <expected_ast>
        <node type="struct" name="ComplexNested">
            <children>
                <node type="struct" name="point">
                    <children>
                        <node type="int" name="x"/>
                        <node type="int" name="y"/>
                    </children>
                </node>
                <node type="union" name="data">
                    <children>
                        <node type="int" name="integer"/>
                        <node type="float" name="floating"/>
                        <node type="struct" name="split">
                            <children>
                                <node type="unsigned int" name="low" bit_size="16"/>
                                <node type="unsigned int" name="high" bit_size="16"/>
                            </children>
                        </node>
                    </children>
                </node>
                <node type="struct" name="matrix">
                    <children>
                        <node type="float" name="values" array_dims="[3,3]"/>
                    </children>
                </node>
                <node type="struct" name="flags">
                    <children>
                        <node type="unsigned int" name="flag1" bit_size="1"/>
                        <node type="unsigned int" name="flag2" bit_size="1"/>
                        <node type="unsigned int" name="" bit_size="6" is_anonymous="true"/>
                        <node type="unsigned int" name="mode" bit_size="4"/>
                    </children>
                </node>
            </children>
        </node>
    </expected_ast>
    <expected_flattened>
        <!-- Point 展平 -->
        <node name="point.x" type="int" offset="0" size="4"/>
        <node name="point.y" type="int" offset="4" size="4"/>
        
        <!-- Union Data 展平 (所有成員 offset=0) -->
        <node name="data.integer" type="int" offset="8" size="4"/>
        <node name="data.floating" type="float" offset="8" size="4"/>
        <node name="data.split.low" type="unsigned int" offset="8" size="2" bit_offset="0" bit_size="16"/>
        <node name="data.split.high" type="unsigned int" offset="8" size="2" bit_offset="16" bit_size="16"/>
        
        <!-- Matrix 展平 -->
        <node name="matrix.values[0][0]" type="float" offset="12" size="4"/>
        <node name="matrix.values[0][1]" type="float" offset="16" size="4"/>
        <node name="matrix.values[0][2]" type="float" offset="20" size="4"/>
        <node name="matrix.values[1][0]" type="float" offset="24" size="4"/>
        <node name="matrix.values[1][1]" type="float" offset="28" size="4"/>
        <node name="matrix.values[1][2]" type="float" offset="32" size="4"/>
        <node name="matrix.values[2][0]" type="float" offset="36" size="4"/>
        <node name="matrix.values[2][1]" type="float" offset="40" size="4"/>
        <node name="matrix.values[2][2]" type="float" offset="44" size="4"/>
        
        <!-- Flags 展平 -->
        <node name="flags.flag1" type="unsigned int" offset="48" size="4" bit_offset="0" bit_size="1"/>
        <node name="flags.flag2" type="unsigned int" offset="48" size="4" bit_offset="1" bit_size="1"/>
        <node name="flags.anonymous_6" type="unsigned int" offset="48" size="4" bit_offset="2" bit_size="6"/>
        <node name="flags.mode" type="unsigned int" offset="48" size="4" bit_offset="8" bit_size="4"/>
    </expected_flattened>
    <expected_layout>
        <total_size>52</total_size>
        <alignment>4</alignment>
    </expected_layout>
</test_case>
```

### 2.3 匿名結構 XML 測試資料
```xml
<test_case name="anonymous_structures">
    <description>匿名結構測試</description>
    <input>
        <![CDATA[
        struct AnonymousTest {
            struct {
                int x;
                char y;
            } anonymous_struct;
            union {
                int i;
                float f;
            } anonymous_union;
            struct {
                unsigned int a : 3;
                unsigned int : 5;
                unsigned int b : 4;
            } anonymous_bitfield;
        };
        ]]>
    </input>
    <expected_ast>
        <node type="struct" name="AnonymousTest">
            <children>
                <node type="struct" name="anonymous_struct" is_anonymous="true">
                    <children>
                        <node type="int" name="x"/>
                        <node type="char" name="y"/>
                    </children>
                </node>
                <node type="union" name="anonymous_union" is_anonymous="true">
                    <children>
                        <node type="int" name="i"/>
                        <node type="float" name="f"/>
                    </children>
                </node>
                <node type="struct" name="anonymous_bitfield" is_anonymous="true">
                    <children>
                        <node type="unsigned int" name="a" bit_size="3"/>
                        <node type="unsigned int" name="" bit_size="5" is_anonymous="true"/>
                        <node type="unsigned int" name="b" bit_size="4"/>
                    </children>
                </node>
            </children>
        </node>
    </expected_ast>
    <expected_flattened>
        <node name="anonymous_struct_1.x" type="int" offset="0" size="4"/>
        <node name="anonymous_struct_1.y" type="char" offset="4" size="1"/>
        <node name="anonymous_union_1.i" type="int" offset="8" size="4"/>
        <node name="anonymous_union_1.f" type="float" offset="8" size="4"/>
        <node name="anonymous_bitfield_1.a" type="unsigned int" offset="12" size="4" bit_offset="0" bit_size="3"/>
        <node name="anonymous_bitfield_1.anonymous_5" type="unsigned int" offset="12" size="4" bit_offset="3" bit_size="5"/>
        <node name="anonymous_bitfield_1.b" type="unsigned int" offset="12" size="4" bit_offset="8" bit_size="4"/>
    </expected_flattened>
</test_case>
```

## 3. 測試案例集合

### 3.1 基本功能測試案例
```python
# 基本功能測試案例
BASIC_TEST_CASES = [
    {
        "name": "simple_struct",
        "input": "struct Simple { int x; char y; };",
        "expected_members": 2,
        "expected_size": 8
    },
    {
        "name": "nested_struct",
        "input": """
        struct Outer {
            struct Inner { int x; } inner;
            int y;
        };
        """,
        "expected_members": 2,
        "expected_flattened": ["inner.x", "y"]
    },
    {
        "name": "union_test",
        "input": """
        struct UnionTest {
            union { int i; float f; } u;
            char c;
        };
        """,
        "expected_members": 2,
        "expected_union_members": ["u.i", "u.f"]
    }
]
```

### 3.2 陣列測試案例
```python
# 陣列測試案例
ARRAY_TEST_CASES = [
    {
        "name": "simple_array",
        "input": "struct ArrayTest { int arr[5]; };",
        "expected_flattened": [
            "arr[0]", "arr[1]", "arr[2]", "arr[3]", "arr[4]"
        ]
    },
    {
        "name": "multi_dimensional_array",
        "input": "struct MultiArray { int matrix[2][3]; };",
        "expected_flattened": [
            "matrix[0][0]", "matrix[0][1]", "matrix[0][2]",
            "matrix[1][0]", "matrix[1][1]", "matrix[1][2]"
        ]
    },
    {
        "name": "nested_struct_array",
        "input": """
        struct NestedArray {
            struct Point { int x; int y; } points[3];
        };
        """,
        "expected_flattened": [
            "points[0].x", "points[0].y",
            "points[1].x", "points[1].y",
            "points[2].x", "points[2].y"
        ]
    }
]
```

### 3.3 位元欄位測試案例
```python
# 位元欄位測試案例
BITFIELD_TEST_CASES = [
    {
        "name": "simple_bitfield",
        "input": """
        struct BitfieldTest {
            unsigned int flags : 4;
            unsigned int mode : 2;
        };
        """,
        "expected_bitfields": [
            {"name": "flags", "bit_size": 4, "bit_offset": 0},
            {"name": "mode", "bit_size": 2, "bit_offset": 4}
        ]
    },
    {
        "name": "anonymous_bitfield",
        "input": """
        struct AnonymousBitfield {
            unsigned int a : 3;
            unsigned int : 5;
            unsigned int b : 4;
        };
        """,
        "expected_bitfields": [
            {"name": "a", "bit_size": 3, "bit_offset": 0},
            {"name": "anonymous_5", "bit_size": 5, "bit_offset": 3},
            {"name": "b", "bit_size": 4, "bit_offset": 8}
        ]
    }
]
```

## 4. 效能測試資料

### 4.1 大型結構生成器
```python
def generate_large_struct(size: int) -> str:
    """生成大型結構用於效能測試"""
    struct_content = f"struct LargeStruct{size} {{\n"
    
    for i in range(size):
        if i % 10 == 0:
            # 每 10 個成員加入一個巢狀結構
            struct_content += f"    struct Nested{i} {{\n"
            struct_content += f"        int nested_x_{i};\n"
            struct_content += f"        char nested_y_{i};\n"
            struct_content += f"    }} nested_{i};\n"
        elif i % 5 == 0:
            # 每 5 個成員加入一個陣列
            array_size = (i % 3) + 2
            struct_content += f"    int array_{i}[{array_size}];\n"
        else:
            # 基本型別成員
            types = ["int", "char", "float", "double"]
            type_name = types[i % len(types)]
            struct_content += f"    {type_name} member_{i};\n"
    
    struct_content += "};"
    return struct_content

# 生成不同大小的測試結構
LARGE_STRUCTS = {
    "small": generate_large_struct(50),      # 50 個成員
    "medium": generate_large_struct(200),    # 200 個成員
    "large": generate_large_struct(500),     # 500 個成員
    "huge": generate_large_struct(1000),     # 1000 個成員
}
```

### 4.2 深度巢狀結構生成器
```python
def generate_deep_nested_struct(depth: int) -> str:
    """生成深度巢狀結構用於壓力測試"""
    struct_content = "struct DeepNested {\n"
    
    for i in range(depth):
        indent = "    " * (i + 1)
        struct_content += f"{indent}struct Level{i} {{\n"
        struct_content += f"{indent}    int value_{i};\n"
        struct_content += f"{indent}    char char_{i};\n"
        
        if i < depth - 1:
            struct_content += f"{indent}    struct Level{i+1} next;\n"
        
        struct_content += f"{indent}}} level{i};\n"
    
    struct_content += "};"
    return struct_content

# 生成不同深度的測試結構
DEEP_NESTED_STRUCTS = {
    "shallow": generate_deep_nested_struct(3),   # 3 層深度
    "medium": generate_deep_nested_struct(5),    # 5 層深度
    "deep": generate_deep_nested_struct(10),     # 10 層深度
    "extreme": generate_deep_nested_struct(20),  # 20 層深度
}
```

## 5. 錯誤處理測試資料

### 5.1 語法錯誤測試案例
```python
# 語法錯誤測試案例
SYNTAX_ERROR_CASES = [
    {
        "name": "missing_semicolon",
        "input": "struct Test { int x }",
        "expected_error": "Missing semicolon"
    },
    {
        "name": "unmatched_braces",
        "input": "struct Test { int x;",
        "expected_error": "Unmatched braces"
    },
    {
        "name": "invalid_type",
        "input": "struct Test { invalid_type x; };",
        "expected_error": "Invalid type"
    },
    {
        "name": "duplicate_member",
        "input": "struct Test { int x; int x; };",
        "expected_error": "Duplicate member name"
    }
]
```

### 5.2 語義錯誤測試案例
```python
# 語義錯誤測試案例
SEMANTIC_ERROR_CASES = [
    {
        "name": "bitfield_too_large",
        "input": "struct Test { unsigned int flags : 33; };",
        "expected_error": "Bitfield size too large"
    },
    {
        "name": "array_zero_size",
        "input": "struct Test { int arr[0]; };",
        "expected_error": "Array size must be positive"
    },
    {
        "name": "circular_reference",
        "input": "struct Test { struct Test self; };",
        "expected_error": "Circular reference detected"
    }
]
```

## 6. 使用範例

### 6.1 基本使用範例
```python
from src.v7.ast_node import ASTNodeFactory
from src.v7.flattening_strategy import StructFlatteningStrategy
from src.v7.parser import V7StructParser

# 建立解析器
parser = V7StructParser()

# 解析結構定義
struct_content = """
struct Example {
    struct Point {
        int x;
        int y;
    } point;
    int value;
};
"""

ast_root = parser.parse_struct_definition(struct_content)

# 展平結構
strategy = StructFlatteningStrategy()
flattened_nodes = strategy.flatten_node(ast_root)

# 輸出結果
for node in flattened_nodes:
    print(f"{node.name}: {node.type} at offset {node.offset}")
```

### 6.2 進階使用範例
```python
# 處理複雜巢狀結構
complex_content = """
struct Complex {
    struct {
        int x;
        char y;
    } anonymous;
    union {
        int i;
        float f;
    } data;
    int arr[2][3];
};
"""

# 解析和展平
ast_root = parser.parse_struct_definition(complex_content)
flattened_nodes = strategy.flatten_node(ast_root)

# 計算佈局
layout_info = strategy.calculate_layout(ast_root)
print(f"Total size: {layout_info['size']}")
print(f"Alignment: {layout_info['alignment']}")

# 生成展平名稱
for node in flattened_nodes:
    name = strategy.generate_name(node)
    print(f"Flattened name: {name}")
```

### 6.3 GUI 整合範例
```python
from src.v7.presenter import V7Presenter

# 建立 Presenter
presenter = V7Presenter()

# 載入結構定義
success = presenter.load_struct_definition(struct_content)
if success:
    # 取得 AST 樹狀結構
    ast_tree = presenter.get_ast_tree()
    
    # 取得展平佈局
    flattened_layout = presenter.get_flattened_layout()
    
    # 切換顯示模式
    presenter.switch_display_mode('tree')
    tree_nodes = presenter.get_display_nodes('tree')
    
    presenter.switch_display_mode('flat')
    flat_nodes = presenter.get_display_nodes('flat')
    
    # 輸出結果
    print("Tree mode nodes:", len(tree_nodes))
    print("Flat mode nodes:", len(flat_nodes))
else:
    print("Failed to load structure definition")
```

---

> 本文件提供 v7 開發的完整範例和測試資料，包含複雜結構範例、XML 測試資料格式、測試案例集合、效能測試資料、錯誤處理測試資料和使用範例。
> 開發時請參考這些範例進行實作和測試。 