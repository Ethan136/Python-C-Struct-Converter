# v5 Nested Structure 支援 TDD 計畫

## 目標
- 讓核心解析與佈局計算能夠處理巢狀 struct（nested struct）。
- 解析 nested struct 後，layout 應遞迴展開並正確計算 offset、padding、alignment。
- GUI 與檔案匯入功能維持相容，不支援的語法需給出清楚錯誤。

## 目前程式碼現況
1. `src/model/struct_parser.py` 中 `MemberDef` 已預留 `nested` 欄位，但尚未解析 nested struct。
2. `layout.StructLayoutCalculator` 僅處理平面成員，未考慮巢狀結構。
3. `StructModel` 與現有測試均假設所有成員在同一層級。
4. 文件與測試 (`tests/README.md`、`STRUCT_PARSING.md`) 皆標示不支援 nested struct。

## TDD 實作規劃
以下步驟皆遵循 **Red → Green → Refactor** 流程。

### 1. 解析階段
1. **新增測試**：`tests/test_struct_parser_v2.py`
   - 新增 `TestParseStructDefinitionV2.test_nested_struct`，輸入包含內嵌 struct 的範例，如：
     ```c
     struct Outer {
         int a;
         struct Inner {
             char b;
             int c;
         } inner;
     };
     ```
   - 驗證 `parse_struct_definition_ast` 回傳的 `StructDef` 中，`members[1].nested` 為 `StructDef`，名稱為 `Inner`，成員數為 2。
   - 初始測試應失敗。
2. **實作解析**：
   - 修改 `struct_parser._extract_struct_body` 與相關函式，能遞迴解析 `struct` 宣告，遇到 `struct` 關鍵字時建立新的 `StructDef` 並存入 `MemberDef.nested`。
   - 保持現有 API，不影響既有功能。
3. **重跑測試**，確認新測試通過並不影響既有測試。

### 2. Layout 計算
1. **新增測試**：`tests/test_struct_model.py`
   - 新增 `TestStructModel.test_calculate_layout_nested`：使用上述 `Outer` 結構，預期 layout 展開後順序為 `a`, `b`, `(padding)`, `c`，並計算總大小與 alignment。
   - 初始測試應失敗。
2. **實作遞迴計算**：
   - 在 `StructLayoutCalculator._process_regular_member` 中檢查 `member.nested`，若存在則遞迴計算內部 layout，並將結果展開插入當前 layout，同時處理 padding 對齊。
   - 回傳的 `LayoutItem` 仍僅包含最終展開的成員，並保留原始名稱格式，例如 `inner.b`、`inner.c`。
3. **確保計算結果** 與 C 編譯器一致，可參考 GCC 生成的 layout 作為比對基準。
4. **重跑測試** 確認通過。

### 3. Hex 解析
1. **新增測試**：`tests/test_struct_model_integration.py`
   - 新增 `test_parse_hex_data_nested`：以 `Outer` 結構及相對應的 hex 資料，驗證 `StructModel.parse_hex_data` 能正確解析 `inner` 成員的值。
   - 初始測試應失敗。
2. **實作支援**：
   - `StructModel.parse_hex_data` 在處理 layout 時本身已依序讀取展開後的欄位，若 layout 計算正確，此處僅需確保欄位名稱包含 `.` 時仍可正確處理。
3. **重跑測試**，確認解析結果正確。

### 4. 文件與限制
1. 更新 `docs/architecture/STRUCT_PARSING.md` 與 `tests/README.md`，描述 nested struct 支援範圍及限制：
   - 僅支援 struct 內直接宣告另一個 struct，暫不支援匿名 struct/union。
   - 手動 struct 模式暫不支援巢狀結構。
2. 為保持本次任務範圍，文件更新可於功能完成後再行補充。

## 待辦與後續工作
- 進一步支援匿名 nested struct、union 及陣列成員等進階語法。
- GUI 顯示與編輯 nested struct 的界面規劃。
- 持續撰寫更多邊界情況測試，確保相容性。

