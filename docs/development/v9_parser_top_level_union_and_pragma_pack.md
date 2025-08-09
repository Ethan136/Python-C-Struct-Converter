# v9 Parser Enhancement Plan

## 背景
- 目前 `V7StructParser` 僅針對以 `struct` 開頭的內容進行解析，遇到 `#pragma pack` 等前置處理指令會提前返回 `None`。
- `_split_member_lines` 在處理多行 `union` 或包含註解的成員時容易將 `union` 切成多段，導致成員解析失敗。
- 無法解析獨立宣告的頂層 `union`，GUI 介面載入 `examples/v5_features_example.h` 時因為 `#pragma pack` 而完全失敗。

## 建議
1. **支援頂層 `union` 解析**：偵測 `union` 關鍵字並透過 `ASTNodeFactory.create_union_node` 建立根節點。
2. **支援前處理 `#pragma` 指令**：能識別並正確處理 `#pragma pack` 等指令，保留對齊設定並確保解析流程不中斷。
3. **改進 `_split_member_lines`**：在遇到巢狀 `struct/union` 時維持完整區塊，避免錯誤拆分。
4. **新增測試案例**：針對上述三點建立單元測試，確保解析器可正確處理。

## 實作步驟
- 重構 `parse_struct_definition`，讓其能同時處理 `struct` 與 `union`。
- 新增 `_handle_directives()` 或於 `_clean_content` 解析 `#pragma` 行，保存 pack 等資訊後再以 `re.search` 找到第一個聚合型別。
- 更新 `_split_member_lines` 判斷邏輯，當偵測到 `union`/`struct` 起始符號 `{` 時累計括號深度，直到對應 `};` 才視為單一成員。
- 在 `tests/model` 下新增：
  - 解析含 `#pragma pack` 的 `struct` 測試。
  - 頂層 `union` 宣告測試。
  - 多行 `union` 或含註解、位元欄位的成員拆分測試。

## 詳細實作
以下列出需調整的檔案與重點內容：
1. **`src/model/parser.py`**
   - `parse_struct_definition` → 改名為 `parse_aggregate_definition` 或內部判斷 `struct/union`。
   - 新增 `_handle_directives()` 於 `_clean_content`，解析並保留 `#pragma` 對齊資訊。
   - `_split_member_lines` → 追蹤括號深度，遇到 `union`/`struct` 直到 `};` 才切分。
2. **`tests/model/test_parser.py`** *(新增/更新)*
   - `test_parse_struct_with_pragma_pack()`：驗證帶有 `#pragma pack` 的檔案可解析。
   - `test_parse_top_level_union()`：驗證頂層 `union` 能建立 AST。
   - `test_split_member_lines_with_union()`：確保多行 `union` 被視為單一成員。
3. **`examples/v5_features_example.h`** *(若必要)*
   - 可新增頂層 `union` 範例或註解說明以輔助測試。

## 需要改動的函式
- `V7StructParser.parse_struct_definition` *(或新 `parse_aggregate_definition`)*
- `V7StructParser._clean_content`
- `V7StructParser._split_member_lines`

## 測試腳本更新細節
- 於 `run_tests.py` 加入新測試路徑，或確保 `pytest` 自動搜尋。
- 測試 `examples/v5_features_example.h`：
  - `#pragma pack` 指令應被解析並套用對齊設定，`struct` 仍能解析。
  - 含有頂層 `union` 時 GUI 亦能載入。
  - 確認 `_split_member_lines` 對含註解、多行或位元欄位的 `union` 可維持完整性。

## TDD 開發規劃
- **撰寫測試先行**：於 `tests/model/test_parser.py` 建立下列失敗測試以明確需求：
  - `test_parse_top_level_union()`：輸入僅含 `union` 的檔案應建立根節點。
  - `test_parse_struct_with_pragma_pack()`：帶有 `#pragma pack(push,1)` 的 `struct` 應以對齊資訊解析。
  - `test_split_member_lines_with_union()`：多行 `union` 或含註解成員應維持單一區塊。
- **逐步實作**：依序加入頂層 `union` 支援、`pragma pack` 處理與 `_split_member_lines` 改寫，使測試逐一轉為通過。
- **重構與覆蓋**：重構程式碼並維持測試覆蓋率，必要時調整既有案例避免重複。

## TDD 開發步驟
1. **頂層 `union` 支援**
   - 建立 `test_parse_top_level_union`，輸入僅含 `union` 的檔案，預期建立 `UnionNode` 根節點。
   - 實作 `parse_aggregate_definition` 或相關判斷邏輯，讓解析器能處理 `union` 並維持 `struct` 原有流程。
   - 重新執行測試，確認其他既有案例仍通過。
2. **`#pragma pack` 指令支援**
   - 撰寫 `test_parse_struct_with_pragma_pack`，包含 `#pragma pack(push,1)` 與對應 `pop`。
   - 擴充 `_handle_directives` 解析並保存對齊資訊，於 AST 節點套用 pack 值。
   - 測試驗證對齊欄位是否與預期一致。
3. **強化 `_split_member_lines`**
   - 新增 `test_split_member_lines_with_union`，測試多行 `union`、註解與位元欄位混合情境。
   - 以括號深度追蹤拆分，確保巢狀聚合型別在 `};` 前都視為同一成員。
   - 處理行內註解與續行符號 `\`，避免誤切。
4. **整合與回歸**
   - 全面執行 `run_tests.py`，確認所有新舊測試皆通過。
   - 觀察覆蓋率，必要時補齊缺漏測試或重構程式碼。

## 更細緻的 TDD 任務拆解
1. **頂層 `union`**
   - *Red*: 建立 `test_parse_top_level_union`，輸入僅含 `union` 定義的檔案，預期產生 `UnionNode` 根節點並以 `assert` 驗證型別與欄位。
   - *Green*: 擴充解析流程偵測 `union` 關鍵字，回傳對應 AST；重跑測試取得綠燈。
   - *Refactor*: 整理 `parse_aggregate_definition` 與相關 helper，確保 `struct/union` 共用邏輯清晰。
2. **`#pragma pack` 指令**
   - *Red*: 寫入 `test_parse_struct_with_pragma_pack`，測試 `#pragma pack(push,1)` 與 `pop` 情境，驗證節點 `pack` 屬性。
   - *Green*: 新增 `_handle_directives` 解析 `#pragma`，維護 pack 堆疊並套用到 AST；讓測試通過。
   - *Refactor*: 將指令解析邏輯抽成獨立函式或類別，並補強錯誤處理與邊界案例。
3. **強化 `_split_member_lines`**
   - *Red*: 新增 `test_split_member_lines_with_union`，包含多行 `union`、巢狀結構與註解，確認拆分結果僅一筆。
   - *Green*: 以括號深度與行續處理重寫 `_split_member_lines`，確保所有測試通過。
   - *Refactor*: 抽出子函式處理註解與續行符號，降低函式複雜度並補上邊界測試。

## 測試案例細節與範例
- `test_parse_top_level_union`
  - **輸入**：
    ```c
    union U {
        int a;
        float b;
    };
    ```
  - **預期**：解析器建立 `UnionNode` 作為根節點，並含有兩個成員。
- `test_parse_struct_with_pragma_pack`
  - **輸入**：
    ```c
    #pragma pack(push,1)
    struct S {
        char c;
        int i;
    };
    #pragma pack(pop)
    ```
  - **預期**：`StructNode` 的 `pack` 屬性為 `1`，並在 `pop` 後恢復預設。
- `test_split_member_lines_with_union`
  - **輸入**：
    ```c
    struct S {
        union {
            int a;
            int b;
        } u;
    };
    ```
  - **預期**：`_split_member_lines` 回傳的列表中，該 `union` 區塊僅佔一個元素，確保後續成員解析不被拆分。

## 迭代提交建議
- **第一階段：頂層 `union` 支援**
  - Commit 1：新增失敗測試 `test_parse_top_level_union`。
  - Commit 2：實作 `parse_aggregate_definition` 以建立 `UnionNode` 根節點。
  - Commit 3：重構共用流程並確保既有測試皆通過。
- **第二階段：`#pragma pack`**
  - Commit 4：新增 `test_parse_struct_with_pragma_pack` 及對齊驗證。
  - Commit 5：導入 `_handle_directives` 並維護 pack 堆疊。
  - Commit 6：整理指令解析函式並補強錯誤處理。
- **第三階段：強化 `_split_member_lines`**
  - Commit 7：新增 `test_split_member_lines_with_union` 與註解/續行案例。
  - Commit 8：以括號深度改寫拆分邏輯並讓測試轉綠。
  - Commit 9：重構子函式降低複雜度，清理重複程式碼。

## 其他考量
- `#pragma pack` 僅影響其後聚合型別，需確認巢狀 `struct/union` 的 pack 繼承與還原邏輯。
- 未來若需支援其他前處理指令，`_handle_directives` 應保留擴充點或以類別方式實作。
- `_split_member_lines` 改寫後應評估效能影響，特別是大型檔案或深度巢狀結構。

---

本文件提出 v9 階段對 Parser 的增強計畫，目標是完整支援 `top level union`、`pragma pack` 及更健壯的 `_split_member_lines` 邏輯，以便在未來 GUI 與 CLI 操作中正確解析更多 C 語言結構。
