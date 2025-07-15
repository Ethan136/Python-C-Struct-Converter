# v5 Union 支援設計與 TDD 計畫

## 1. 目標
- 讓核心模組能解析、計算並處理 C 語言 `union`，行為與既有 `struct` 功能一致。
- 全程以 TDD 流程實作，新增功能皆需先撰寫對應測試。

## 2. 現況檢查
- `src/model/layout.py` 已實作 `UnionLayoutCalculator`，但 `calculate_layout` 與 `StructModel` 尚未使用。
- `src/model/struct_parser.py` 目前只有 `parse_struct_definition*` 系列函式；`parse_c_definition` 與 `parse_c_definition_ast` 僅處理 `struct`。
- 測試層僅有 `tests/test_union_preparation.py`，用來驗證目前只支援 `struct`。

## 3. 待修改項目
1. **Parser 層**
   - 新增 `parse_union_definition`、`parse_union_definition_v2` 及 `parse_union_definition_ast`，流程與 struct 版本相同但使用 `keyword="union"`。
       - 位置：`src/model/struct_parser.py`，於現有 `parse_struct_definition` 系列函式附近新增。
       - 可複製 `parse_struct_definition`、`parse_struct_definition_v2`、`parse_struct_definition_ast` 的實作並將 `_extract_struct_body` 的 `keyword` 參數改為 "union"，回傳 `UnionDef` 物件。
   - 更新 `parse_c_definition`、`parse_c_definition_ast`：偵測開頭關鍵字回傳 `('union', name, members)` 或對應的 `UnionDef`。
       - 於 `src/model/struct_parser.py` 修改 `parse_c_definition`(約184行) 及 `parse_c_definition_ast`(約196行)。
       - 透過 `re.match("\s*(struct|union)\s+")` 判斷宣告類型後，分別呼叫 `parse_struct_definition*` 或 `parse_union_definition*`。
   - 確認 `_extract_struct_body` 已支援 `keyword` 參數並供兩種宣告共用。
       - `_extract_struct_body` 已包含 `keyword` 參數，目前定義於約118行，兩種宣告共用此函式即可。

       - 在 `src/model/__init__.py` 的 `__all__` 列表加入 `parse_union_definition`, `parse_union_definition_v2`, `parse_union_definition_ast`, 以及 `UnionDef`。

2. **Layout 計算**
   - `calculate_layout` 增加 `kind` 或 `calculator_cls` 判斷，根據解析結果選用 `StructLayoutCalculator` 或 `UnionLayoutCalculator`。
       - 在 `src/model/struct_model.py` 的 `calculate_layout` 函式加入 `kind` 參數，
         預設為 `None`，若值為 "union" 則改用 `UnionLayoutCalculator`。
       - `StructModel.load_struct_from_file` 需先呼叫 `parse_c_definition_ast` 確認回傳型別，
         再依照 `StructDef` 或 `UnionDef` 使用對應 calculator 並記錄 `self.kind`。

3. **Hex 資料解析**
   - `parse_hex_data` 流程不需特別調整，因為 union 成員皆位於 offset=0，只需依照計算好的 layout 讀取即可。
       - 主要程式碼位於 `StructModel.parse_hex_data` (約60行)。因 layout 結構相同，無需因 union 額外調整。


4. **文件與測試**
   - 更新 `docs/architecture/STRUCT_PARSING.md` 與 `examples/README.md`，移除「不支援 union」的描述並加入範例。
   - README 需新增 union 支援說明。

       - 移除 `STRUCT_PARSING.md` 第 7 行與 132~133 行關於不支援 union 的敘述，並補充 union 佈局規則。
       - `examples/README.md` 第 10 行刪除不支援 union 的描述，改以簡短說明支援 union 範例檔。
       - `README.md` Features 與說明部分需新增 union 功能介紹。

## 4. TDD 流程與新增測試
1. **解析相關測試**
   - 新增 `tests/test_union_parser.py`
       1. `test_parse_union_definition`：輸入簡易 union 宣告，期待 `parse_c_definition` 回傳 `('union', 'U', ...)`。
       2. `test_parse_union_definition_ast`：驗證 `UnionDef` 回傳內容。
2. **Layout 計算測試**
   - 新增 `tests/test_union_layout.py`
       1. 使用 `UnionLayoutCalculator`，確認 layout 中每個成員 offset 皆為 0。
       2. 驗證總大小為所有成員 size 最大值，alignment 為最大對齊值。
3. **StructModel 整合測試**
   - 新增 `tests/test_union_integration.py`
       1. 透過 `StructModel.load_struct_from_file` 讀取 union，檢查產生的 layout、`total_size` 與 `struct_align`。
       2. 使用 `StructModel.parse_hex_data` 還原 union 成員值，確認值正確解析。
4. **更新既有測試**
   - `tests/test_union_preparation.py` 改寫為一般功能測試，驗證 `calculate_layout` 可接受 `calculator_cls=UnionLayoutCalculator` 並正確運作。
5. **測試執行**
   - 每項功能完成後執行 `run_all_tests.py`，確保新舊測試皆通過。

## 5. 範例測試案例
```c
union U {
    int a;
    char b;
};
```
- layout 應只有兩個成員且 offset 皆為 0。
- `total_size` 為較大成員 (`int`) 的大小，在 64 位系統為 4 bytes。
- endianness 仍由 `parse_hex_data` 控制。

---
完成以上項目後，專案將能完整支援 C 語言 `union`，並維持 TDD 流程與既有模組相容性。
