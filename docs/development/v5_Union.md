# v5 Union 支援設計與 TDD 計畫

## 1. 目標
- 讓核心模組能解析、計算並處理 C 語言 `union`，與既有 `struct` 功能一致。
- 以 TDD 流程實作，確保所有新增行為皆有測試覆蓋。

## 2. 現況檢查
- `src/model/layout.py` 已有 `UnionLayoutCalculator`，但尚未整合至 `calculate_layout`。
- `src/model/struct_parser.py` 只有 `parse_struct_definition`，`parse_c_definition` 也僅回傳 `struct`。
- 測試僅包含 `tests/test_union_preparation.py`，驗證目前只支援 `struct`。

## 3. 待修改項目
1. **Parser 層**
   - 新增 `parse_union_definition` 與 `parse_union_definition_v2`，可解析 `union U { ... };`。
   - `parse_c_definition`、`parse_c_definition_ast` 需能判斷並回傳 `union` 或 `struct`。
   - `_extract_struct_body` 函式須接受 `keyword` 參數以支援 `union`。目前已有此參數，可直接沿用。
2. **Layout 計算**
   - `calculate_layout` 增加選擇 `StructLayoutCalculator` 或 `UnionLayoutCalculator` 的邏輯。
   - `StructModel` 在載入檔案時依據型別呼叫對應 calculator。
3. **Hex 資料解析**
   - `parse_hex_data` 對於 union 僅需解析 offset=0 的單一儲存空間，可沿用現有流程。
4. **測試與文件**
   - 依照 TDD 流程，逐步新增單元測試後才撰寫實作。
   - 補充文件與 README，說明已支援 union。

## 4. TDD 流程建議
1. **解析測試**
   - 新增 `tests/test_union_parser.py`：
       1. 撰寫測試 `test_parse_union_definition`，期待 `parse_c_definition` 回傳 `('union', 'U', members)`。
       2. 測試失敗後，實作 `parse_union_definition` 等函式。
2. **Layout 測試**
   - 新增 `tests/test_union_layout.py`：
       1. 使用 `UnionLayoutCalculator` 驗證成員大小最大值即為 union 總大小。
       2. 驗證 alignment 取成員最大對齊值。
3. **StructModel 整合測試**
   - 於 `tests/test_union_integration.py`：
       1. 測試 `StructModel.load_struct_from_file` 能處理 union，並正確產生 layout、total_size。
       2. 測試 `parse_hex_data` 在 union 情境下可解析各成員值。
4. **更新舊測試**
   - 調整 `test_union_preparation.py`，改為驗證 union 功能而非預期失敗。
5. **文件與範例**
   - 更新 `README.md` 及相關開發文檔，新增 union 範例與使用說明。
6. **執行 `run_all_tests.py`**
   - 每完成一個步驟即執行全測試，確保未破壞既有功能。

## 5. 範例測試案例
```c
union U {
    int a;
    char b;
};
```
- layout 應只有兩個成員，offset 皆為 0。
- total_size 為較大型別 (`int`) 的大小，若在 64 位系統即 4 bytes。
- endianness 依舊由 `parse_hex_data` 處理。

---

此計畫完成後，專案將能完整支援 C 語言 union，並維持既有 TDD 流程與高覆蓋率測試。
