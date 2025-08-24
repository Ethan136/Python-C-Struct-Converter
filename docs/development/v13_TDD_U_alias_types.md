# v13 – TDD 計畫：支援 U8/U16/U32/U64（對應 unsigned 1/2/4/8 bytes)

本文定義針對 U8/U16/U32/U64 的解析與佈局支援之 TDD 測試策略、案例矩陣與完成標準。

## 目標與範圍

- 解析層（parser）：能將 U8/U16/U32/U64 正規化為對應標準型別
  - U8 → `unsigned char`
  - U16 → `unsigned short`
  - U32 → `unsigned int`
  - U64 → `unsigned long long`
- 佈局層（layout）：`TYPE_INFO` 具有 U8/U16/U32/U64 的 size/align，佈局結果與對應無號型別一致。
- bitfield：`U32 x : 3;`、`U8 y : 1;` 等等行為需等同於 `unsigned int` / `unsigned char` 的 bitfield 規則（允許、packing 與 bit_offset 正確）。
- AST/巢狀/陣列：在巢狀結構、union 以及陣列情境中皆能正確解析與計算。

## 驗收標準（Acceptance Criteria）

1. `parse_member_line_v2` 對以下輸入皆回傳 `MemberDef` 且 type 為對應的標準無號型別：
   - `U8 a;` → `unsigned char`
   - `U16 b;` → `unsigned short`
   - `U32 c;` → `unsigned int`
   - `U64 d;` → `unsigned long long`
   - 陣列：`U16 arr[3];` → `array_dims=[3]`
   - bitfield：`U32 f : 3;`、`U8 g : 1;` → `is_bitfield=True` 與 `bit_size` 正確
2. `parse_struct_definition_ast` 能解析含 Ux 型別的巢狀 struct/union，並在 `MemberDef` 中呈現正確 type 與 `array_dims`/`nested`。
3. `calculate_layout` 對含 Ux 型別之 struct 計算的 size/align/offset 與對應無號型別相同。
4. bitfield packing：連續 `U32` bitfield 的 `bit_offset` 正確累加，跨 storage unit 時開新單元並依 alignment 對齊；`U8` bitfield 以 1 byte 為 storage unit。
5. End-to-end：從 `.h` 檔讀入使用 Ux 型別的範例，GUI 顯示的 Struct Layout 與解析出的值（在零值情況）皆合理且無例外。
6. 負向案例：未知型別（如 `U128`）應被拒絕或略過，且不造成例外。

## 測試矩陣與案例

位置建議（可依現有測試結構微調）：

- 檔案：`tests/model/test_struct_parser_v2.py`
  - `test_parse_member_line_aliases_basic()`：U8/U16/U32/U64 一般成員 → type 正規化
  - `test_parse_member_line_aliases_array()`：`U16 arr[3];` → `array_dims=[3]`
  - `test_parse_member_line_aliases_bitfield()`：`U32 f : 3;`、`U8 g : 1;` → `is_bitfield=True`
  - `test_parse_struct_definition_ast_with_aliases()`：巢狀 + 陣列 + bitfield 綜合
  - `test_unknown_alias_rejected()`：`U128 x;` 行為（預期：不支援 → 不產生 `MemberDef` 或丟出明確錯誤）

- 檔案：`tests/model/test_struct_parsing_core.py`
  - `test_layout_with_aliases_sizes_and_offsets()`：
    ```c
    struct A {
        U8  a;   // 1 byte
        U32 b;   // 4 bytes, alignment 4 → 需要 padding
        U16 c;   // 2 bytes
        U64 d;   // 8 bytes, alignment 8
    };
    ```
    驗證：offset 與 size 與 `unsigned char/int/short/unsigned long long` 對應一致。
  - `test_layout_with_alias_bitfields_packing()`：
    ```c
    struct B {
        U32 f1 : 3;  // bit_offset 0
        U32 f2 : 5;  // bit_offset 3
        U32 f3 : 24; // 跨 storage 行為驗證（可視需求）
        U8  g1 : 1;  // 新 storage，對齊 1 byte
        U8  g2 : 2;  // bit_offset 1
    };
    ```

- 檔案：`tests/integration/test_struct_model_integration.py`
  - `test_integration_alias_types_from_header()`：從 `.h` 載入含 Ux 型別的範例，驗證 layout 與解析零值行為。

## 實作步驟（TDD 流程）

1. 寫 `test_parse_member_line_aliases_basic()`（失敗）
2. 在 parser 增加 alias 對映與 `TYPE_INFO` 增列（最小變更），使之通過
3. 寫 array 與 bitfield 相關測試（失敗）
4. 確認 parser bitfield 分支能在 alias 正規化後仍走原規則（若需，調整順序）
5. 寫 layout 尺寸/位移與 bitfield packing 測試（失敗）
6. 擴充 `TYPE_INFO` 與佈局計算，使測試通過
7. 寫 AST/巢狀/整合測試（失敗）
8. 驗證 AST 解析後的 members 會被正確傳入 `calculate_layout`（必要時調整）
9. 收尾：負向案例、邊界條件、文件更新

## 風險與緩解

- 別名需在 bitfield 檢查前正規化：避免 `U32 f:3` 被誤判為不支援型別。
- GUI 舊有快取或重繪邏輯干擾觀察：新增單元測試優先、GUI 僅作 smoke 驗證。
- 型別對齊在不同平台差異：目前以 x86_64 常見值為準（同 `TYPE_INFO` 註解），若要擴充以 pragma/pack 另行追蹤。

## 完成定義（Definition of Done）

- 上列單元/整合測試均綠燈；
- `examples/` 新增一個含 Ux 型別的最小範例檔（必要時）；
- 文件更新（本文件 + 架構/解析文件必要處）完成；
- CI 與手動在 macOS 本機驗證通過，GUI smoke 測試無例外。
