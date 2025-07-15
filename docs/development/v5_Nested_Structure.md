# v5 Nested Structure 支援 TDD 計畫

## 目標
- 讓核心解析與佈局計算能夠處理巢狀 struct（nested struct）。
- 解析 nested struct 後，layout 應遞迴展開並正確計算 offset、padding、alignment。
- GUI 與檔案匯入功能維持相容，不支援的語法需給出清楚錯誤。

## 目前程式碼現況
1. `src/model/struct_parser.py` 中 `MemberDef` 已預留 `nested` 欄位，但尚未解析 nested struct。
   - 定義位置：`struct_parser.py` **8-21 行**【F:src/model/struct_parser.py†L8-L21】。
   - `_extract_struct_body` 於 **118-143 行** 僅回傳最外層 body，未處理巢狀宣告【F:src/model/struct_parser.py†L118-L143】。
   - `parse_struct_definition_v2`/`parse_struct_definition_ast` (161-182 行) 也未遞迴處理【F:src/model/struct_parser.py†L161-L182】。
2. `layout.StructLayoutCalculator` 僅處理平面成員，未考慮巢狀結構。
   - `_process_regular_member` 於 **160-181 行** 直接加入成員，不展開子 struct【F:src/model/layout.py†L160-L181】。
3. `StructModel` 與現有測試均假設所有成員在同一層級。
   - `parse_hex_data` (60-105 行) 逐行讀取展開後 layout，尚無支援 `.` 層級名稱【F:src/model/struct_model.py†L60-L105】。
4. 文件與測試 (`tests/README.md`、`STRUCT_PARSING.md`) 皆標示不支援 nested struct。

## 主要修改模組
- `src/model/struct_parser.py`：遞迴解析巢狀 `struct`，於 `MemberDef.nested` 儲存 `StructDef` 物件。
  - 主要調整 `_extract_struct_body` 與 `parse_struct_definition_v2` (118-182 行)。
- `src/model/layout.py`：`StructLayoutCalculator._process_regular_member` 需能展開內嵌成員並處理對齊。
  - 修改位置約在 **160 行** 之後，加入 `member.nested` 判斷。
- `src/model/struct_model.py`：`parse_hex_data` 在讀取 layout 時支援以 `.` 分隔的欄位名稱。
  - 相關程式碼位於 **60-105 行**。
- 測試與範例檔需新增 nested struct 用的 `.h` 檔案。

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
   - 修改 `struct_parser._extract_struct_body` 與 `parse_member_line_v2` 讓解析流程遇到 `struct` 關鍵字時會呼叫 `parse_struct_definition_ast` 再存入 `MemberDef.nested`。
   - 主要邏輯寫在 `parse_struct_definition_v2` 補上遞迴處理，保持現有 API。
3. **重跑測試**，確認新測試通過並不影響既有測試。

### 2. Layout 計算
1. **新增測試**：`tests/test_struct_model.py`
   - 新增 `TestStructModel.test_calculate_layout_nested`：使用上述 `Outer` 結構，預期 layout 展開後順序為 `a`, `b`, `(padding)`, `c`，並計算總大小與 alignment。
   - 初始測試應失敗。
2. **實作遞迴計算**：
   - 在 `StructLayoutCalculator._process_regular_member` (160 行起) 檢查 `member.nested`，若存在則遞迴計算內部 layout 並展開結果。
   - 插入展開成員時需沿用 `inner.<name>` 命名並處理 padding 對齊。
   - 回傳的 `LayoutItem` 僅包含展開後的成員，例如 `inner.b`、`inner.c`。
3. **確保計算結果** 與 C 編譯器一致，可參考 GCC 生成的 layout 作為比對基準。
4. **重跑測試** 確認通過。

### 3. Hex 解析
1. **新增測試**：`tests/test_struct_model_integration.py`
   - 新增 `test_parse_hex_data_nested`：以 `Outer` 結構及相對應的 hex 資料，驗證 `StructModel.parse_hex_data` 能正確解析 `inner` 成員的值。
   - 初始測試應失敗。
2. **實作支援**：
   - `StructModel.parse_hex_data` 在處理 layout 時本身已依序讀取展開後的欄位，若 layout 計算正確，此處僅需確保欄位名稱包含 `.` 時仍可正確處理。
   - 主要修改範圍為 `parse_hex_data` **60-105 行**，僅需在 append 結果時保留全名。
3. **重跑測試**，確認解析結果正確。

## 新增/調整的測試檔案
- `tests/data/test_nested_struct.h`：範例巢狀結構檔案供單元測試載入。
- `tests/test_struct_parser_v2.py`：新增 nested struct 解析測試案例。
- `tests/test_struct_model.py`：新增 layout 計算測試 `test_calculate_layout_nested`。
- `tests/test_struct_model_integration.py`：新增 `test_parse_hex_data_nested` 驗證整合流程。

### 4. 文件與限制
1. 更新 `docs/architecture/STRUCT_PARSING.md` 與 `tests/README.md`，描述 nested struct 支援範圍及限制：
   - 僅支援 struct 內直接宣告另一個 struct，暫不支援匿名 struct/union。
   - 手動 struct 模式暫不支援巢狀結構。
2. 為保持本次任務範圍，文件更新可於功能完成後再行補充。

## 待辦與後續工作
- 進一步支援匿名 nested struct、union 及陣列成員等進階語法。
- GUI 顯示與編輯 nested struct 的界面規劃。
- 持續撰寫更多邊界情況測試，確保相容性。

