## v18 - Import .H 支援頂層 `#pragma pack(push/pack/pop)`（TDD 開發計畫）

### 背景與目標
- 目前 Import .H 頁簽採用 AST 路徑（`src/model/struct_parser.py` → `StructModel.load_struct_from_file`），未解析或傳遞頂層 `#pragma pack(push/pack/pop)` 對齊設定，導致 layout 未套用 pack 對齊。
- v18 目標：在 Import .H 功能中支援頂層 `#pragma pack(push, N)`、`#pragma pack(N)` 與 `#pragma pack(pop)`，將有效 pack 對齊值傳遞至 layout 計算，使結果與編譯器行為一致（以 min(alignment, pack) 準則）。

### 範圍定義
- 僅處理「頂層」pragma：即出現在第一個被選取之頂層聚合（struct/union）之前的 pragma 指令；巢狀宣告內部的 pragma 不在本次範圍。
- 支援指令型式：
  - `#pragma pack(push, N)` 多層堆疊
  - `#pragma pack(N)` 設定當前 pack（等效 push 無名層，或直接覆寫；本次以「覆寫當前有效值」處理）
  - `#pragma pack(pop)` 退回上一層設定
- 只影響 Import .H AST 流程的 layout 計算，不改變 v7 專屬解析器既有行為。

### TDD 流程（Red → Green → Refactor）
1) Red：新增（或擴充）測試，驗證 Import .H 流程會將 pack 對齊影響傳至 layout。
   - `tests/model/test_struct_model_import_pack.py`
     - `test_import_h_applies_top_level_pack_push_1`
     - `test_import_h_applies_top_level_pack_push_nested_push_pop`
     - `test_import_h_applies_top_level_pack_single_pack_syntax`
     - `test_import_h_ignores_trailing_pop_without_push`
     - `test_import_h_select_target_struct_with_pack`
   - 若已有 `examples/` header，可複用或新增最小化測試字串（避免依賴外檔）。

2) Green：最小實作使測試通過。
   - 在 Import .H AST 路徑解析「頂層 pragma 對齊」並傳入 `calculate_layout(..., pack_alignment=...)`：
     - 選項 A（建議）：在 `src/model/struct_model.py::load_struct_from_file` 中新增 `_extract_top_level_pack_alignment(content)`，只掃描第一個被解析聚合之前的 pragma 區段，維護 push/pack/pop 堆疊並回傳當前有效值。
     - 選項 B：在 `src/model/struct_parser.py` 新增 `_extract_top_level_pack_alignment(file_content)` helper，並在 `StructModel` 呼叫，保持 parser 與 model 邏輯分離可視團隊偏好。
   - 於 AST 路徑（`definition and hasattr(definition, 'members')` 分支）將回傳的 `pack_alignment` 傳入 `calculate_layout(self.members, pack_alignment=pack)`。
   - 更新 layout 已支援 pack（`src/model/layout.py` 已有 `_effective_alignment` 最小實作）；確認 struct/union/array/bitfield 佈局計算皆使用 `_effective_alignment`。

3) Refactor：
   - 將 `_extract_top_level_pack_alignment` 測試化與文件化，保留錯誤處理（不合法的 pop、非數字參數）以警告或忽略，不中斷 Import 流程。
   - 文件補充：在 `docs/architecture/STRUCT_PARSING.md` 與 v18 變更說明中加入 pack 支援與限制（僅頂層，巢狀略）。

### 需要改動的檔案與位置
- `src/model/struct_model.py`
  - `load_struct_from_file(...)`：
    - 在 AST 成功路徑中，計算 `pack_alignment = _extract_top_level_pack_alignment(content, target_name)`，傳入 `calculate_layout(self.members, pack_alignment=pack_alignment)`。
  - 新增 helper：`_extract_top_level_pack_alignment(content: str, target_name: Optional[str]) -> Optional[int]`
    - 僅掃描「第一個將被選取之聚合（struct/union）」前綴文字的 pragma，維護堆疊：
      - `#pragma pack(push, N)` → `stack.append(N)`
      - `#pragma pack(N)` → 若 `stack` 非空，覆寫 `stack[-1] = N`；否則 `stack.append(N)`（採一致覆寫行為）
      - `#pragma pack(pop)` → `stack.pop()`（如為空則忽略並記錄警告）
    - 允許空白、大小寫變化，N 為十進位數字。

- `src/model/layout.py`
  - 確認 `_effective_alignment` 與對齊計算一致，已存在：`min(alignment, pack_alignment)`；如必要，補齊在 union/array/bitfield 路徑也使用此規則。

- `src/model/struct_parser.py`
  - 無需修改 AST 結構；僅在需要時提供取得第一個被選取之聚合起點的輔助函式（可選）。

### 新增測試清單與驗證點
- 檔案：`tests/model/test_struct_model_import_pack.py`

1. `test_import_h_applies_top_level_pack_push_1`
   - 內容：
     ```c
     #pragma pack(push,1)
     struct S { char c; int i; };
     ```
   - 驗證：
     - 透過 `StructModel.load_struct_from_file`（或以字串版本 helper）載入，layout 中 `i` 的 offset 為 1（因 pack=1），總大小符合壓縮對齊。

2. `test_import_h_applies_top_level_pack_push_nested_push_pop`
   - 內容：
     ```c
     #pragma pack(push,1)
     #pragma pack(push,4)
     struct A { int x; char y; };
     #pragma pack(pop)
     struct B { int x; };
     ```
   - 驗證：
     - 指定 `target_name='A'` 時，pack=4 生效；指定 `target_name='B'` 時，pack 恢復至 1 或 None（依堆疊邏輯）。

3. `test_import_h_applies_top_level_pack_single_pack_syntax`
   - 內容：
     ```c
     #pragma pack(2)
     struct S { char c; int i; };
     ```
   - 驗證：
     - 有效 pack=2；offset 與 total size 依 min(alignment, 2) 計算。

4. `test_import_h_ignores_trailing_pop_without_push`
   - 內容：
     ```c
     #pragma pack(pop)
     struct S { int i; };
     ```
   - 驗證：
     - 不拋例外；等同無 pack 情況；可透過 logger mock 驗證警告（選擇性）。

5. `test_import_h_select_target_struct_with_pack`
   - 內容：同一檔案多個頂層 struct，前綴含多層 push/pack/pop；
   - 驗證：
     - 使用 `set_import_target_struct(name)` 切換時，對應目標 struct 的有效 pack 正確計算並影響 layout。

6. 進階覆蓋（array/bitfield/union）
   - `test_import_h_pack_effect_on_array_elements`
     - 內容：
       ```c
       #pragma pack(2)
       struct S { short s; int arr[2]; };
       ```
     - 驗證：`arr[0]` offset 以 2 對齊而非 4；總大小符合 pack=2。
   - `test_import_h_pack_effect_on_bitfields`
     - 內容：
       ```c
       #pragma pack(1)
       struct S { unsigned int a:3; unsigned int b:5; unsigned int c:8; };
       ```
     - 驗證：bitfield 單元以對應基本型別對齊，且最終 struct 對齊/大小受 pack=1 限制。
   - `test_import_h_pack_effect_on_nested_union`
     - 內容：
       ```c
       #pragma pack(1)
       struct S { union { int x; char y[4]; } u; char t; };
       ```
     - 驗證：`u` 對齊以 min(align(int), 1) 計算；`t` 的 offset 與尾端 padding 受 pack 影響。

### 實作細節建議
- 以 regex 掃描 pragma 指令，範例：
  - `r"#pragma\s+pack\s*\(\s*(?:push\s*,\s*(\d+)|pop|(\d+))\s*\)"`，群組1=push 值、群組2=單一 pack 值；大小寫忽略。
- 決定目標聚合起點：
  - 若 `target_name` 指定：從 `struct_parser._extract_struct_body_by_name` 尋得的起點位置往前取 prefix；
  - 否則：沿用 AST 預設選擇邏輯（最後一個頂層 struct 或 union），在同檔內以 brace-depth 過濾尋得之第一個被 Import 流程採用的聚合，取其起點位置往前作為 prefix。
- 安全性：遇到語法不符或越界 pop，記錄 warning 並忽略，不中止流程。

### 文件與維護
- 更新 `docs/architecture/STRUCT_PARSING.md`：加入「Import .H 頂層 pragma 支援」章節，說明有效範圍與限制。
- 在 `README.md` 的功能列表中新增說明：Import .H 支援 `#pragma pack(push/pack/pop)`（頂層）。
- 在 `examples/` 增補一個 `v18_pack_examples.h` 展示最小案例（非必須，測試可用內嵌字串）。

### 風險與回退策略
- 風險：選定「第一個被採用的聚合」與 pragma prefix 邊界判定出錯，導致 pack 取值不正確。
- 降風險：以測試覆蓋多頂層 struct/union、push/pack 混用、孤立 pop、`target_name` 切換等情境。
- 回退：若 AST 導入 pack 失敗，不影響 legacy 解析回退路徑；可在配置中關閉此功能（未納入本次範圍，可於 v18.x 評估）。

### 交付定義（Definition of Done）
- 新增的單元測試全部通過，且既有測試不退步。
- Import .H 載入含 pragma 的 .h 後，layout 與主流編譯器行為一致（以簡例人工驗證）。
- 文件與變更記錄完成，後續開發者可依此文件實作與維護。

