## v15 2D Array Import .h Fix — array-of-pointer lost dimensions

### 問題描述
- 解析 `examples/v14_features_example.h` 中的 `U8* arr2d[2][3];`（2x3 的二維陣列，元素型別為指標）。
- GUI 佈局與值面板顯示時，`arr2d` 被視為「單一欄位（pointer）」而非展開為 `arr2d[0][0]`...`arr2d[1][2]`。
- 在「Struct Layout」區塊看到的型別是 `pointer`，`Size=4`（32-bit 模式），沒有逐一展開的元素。

### 預期行為
- `arr2d` 應展開為 6 個元素：`arr2d[0][0]`、`arr2d[0][1]`、`arr2d[0][2]`、`arr2d[1][0]`、`arr2d[1][1]`、`arr2d[1][2]`。
- 每個元素的型別都應是 `pointer`，大小等於目前指標模式的位元組數（32-bit/64-bit 可切換）。

### 根因分析
解析流程關鍵在 `src/model/struct_parser.py` 的 `parse_member_line`。當偵測到型別字串含有 `*`（指標）時，現行邏輯直接回傳一個 tuple `("pointer", name)`，導致「任何陣列維度」在這一分支被丟失。

下方為相關程式片段（指標分支會提早 return，未帶出 `array_dims`）：

```127:137:src/model/struct_parser.py
    member_match = re.match(r"(.+?)\s+([\w\[\]]+)$", line)
    if member_match:
        type_str, name_token = member_match.groups()
        clean_type = normalize_type(" ".join(type_str.strip().split()))
        name, dims = _extract_array_dims(name_token)
        if "*" in clean_type:
            return ("pointer", name)
        if clean_type in TYPE_INFO:
            if dims:
                return {"type": clean_type, "name": name, "array_dims": dims}
            return (clean_type, name)
```

因此，像 `U8* arr2d[2][3];` 這種「指標元素的陣列」會被解析成「單一指標欄位」，`array_dims` 遺失，後續 `layout` 就無法展開為多個元素。

### 建議修正
最小變更（不影響既有單一指標欄位的輸出型別）如下：

1) 僅在偵測到指標且存在陣列維度時，改為回傳 dict，保留 `array_dims`：

```python
# in parse_member_line, replace the pointer early-return
if "*" in clean_type:
    if dims:
        return {"type": "pointer", "name": name, "array_dims": dims}
    return ("pointer", name)
```

2) 其餘流程不需修改：
- `parse_member_line_v2` 會把 dict 轉為 `MemberDef`，包含 `array_dims`。
- `StructLayoutCalculator._process_array_member` 已支援多維展開；當 `mtype == "pointer"` 時，會按指標大小為每個元素新增佈局項目。

### 影響面與相容性
- 單一指標欄位（無陣列）維持回傳 tuple（`("pointer", name)`），對舊路徑與既有測試無破壞性。
- 陣列（含 N-D 陣列）的指標欄位會正確展開為 `arr[i][j]` 等元素。
- 巢狀 struct/union 與多維陣列的其他情境不受影響；`layout` 的展開邏輯已覆蓋。

### 測試建議
- 單元測試（新增於 `tests/model`）：
  - 解析 `U8* arr2d[2][3];`，檢查 `layout` 產出包含 6 個元素：`arr2d[0][0]` ... `arr2d[1][2]`，型別皆為 `pointer`，大小為指標大小。
  - 解析 `struct S* p[2];`（指向 struct 的指標陣列），同樣應展開為 `p[0]`、`p[1]`，型別為 `pointer`。
- 整合測試（Presenter）：載入示例頭檔後，`get_display_nodes("tree")` 於 `arr2d` 節點下可見 6 個子節點。

### 非目標（本次不處理）
- 如 `U8 (*arr2d)[3];`（「指向一維陣列的指標」）這類宣告的解析與呈現；屬不同語意，若後續需要再評估。

### 備註
- `examples/v14_features_example.h` 中 `U8/U16/U32` 的型別別名由系統型別表提供，雖然靜態 linter 無法識別，但不影響解析與佈局計算。

---

### 架構評估：最小改動 vs. 資料格式統一

本次建議的修正只動到 parser 的單一分支（指標 early-return），屬於「最小改動」。從架構可維度評估如下：

1) 最小改動（本提案）
   - 優點：
     - 觸及範圍小，不影響既有 `tuple` 與 `dict` 混用的 legacy 支援邏輯。
     - 與既有 `layout`/`presenter` 完全相容，風險低。
     - 立即解決「指標陣列維度遺失」的實際問題。
   - 風險/成本：
     - `parse_member_line` 仍然會回傳兩種型別（tuple 或 dict），需靠 `calculate_layout` 內部去兼容，技術負債繼續存在。

2) 資料格式統一（替代方案，較大改動）
   - 方向：
     - 讓 `parse_member_line` 一律回傳結構化物件（如 `MemberDef` 或嚴格的 dict），不再回傳 tuple。
     - 指標、基本型別、bitfield、陣列皆以單一格式攜帶欄位（`type/name/is_bitfield/bit_size/array_dims/nested`）。
   - 優點：
     - 移除格式分歧，`layout.calculate` 不需再判斷 tuple/dict/AST 多種格式，簡化維護與型別安全。
     - 後續（v16 引用型 struct/union 解析、更多宣告語法）擴充更順暢。
   - 風險/成本：
     - 波及面大：`struct_model.calculate_layout`、既有測試、可能的匯出/匯入流程都要同步更新。
     - 需要一次性調整與回歸驗證，短期交付風險較高。

3) 折衷方案（建議路線圖）
   - v15：採最小改動解 bug，確保 N-D 指標陣列可正確展開。
   - v16：落實引用型 struct/union 的解析（見 v16 文件），不依賴資料格式大改。
   - v17：啟動「資料格式統一」重構：
     - `parse_member_line_v2`/`parse_struct_definition_v2` 全面輸出 `MemberDef`。
     - `calculate_layout` 僅接受 `MemberDef`（保留舊 API 的薄 wrapper 轉換）。
     - 漸進淘汰 tuple/dict 路徑，刪除多餘分支與轉換邏輯。

### 結論與建議
- 以風險控管與交付效率考量，v15 採用「最小改動」最合適，能即時修正 GUI 顯示與 layout 展開問題。
- 中長期建議在 v17 啟動資料格式統一，降低 parser → model → layout 的型別分歧，提升整體兼容性與可維護性。

---

### TDD 開發計畫（v15）

目標：修正「指標元素的多維陣列」在解析時遺失 `array_dims` 的問題，並確保 GUI 展示與 layout 正確展開。

1) 測試清單（先寫測試再實作）
   - 單元測試：`tests/model/test_struct_parser_v15_pointer_array.py`
     - `test_pointer_2d_array_dims_preserved`：
       - 輸入：`struct S { U8* arr2d[2][3]; };`
       - 期望：AST/member 或中介結果包含 `array_dims=[2,3]`，`type=="pointer"`，`name=="arr2d"`。
     - `test_pointer_1d_array_dims_preserved`：
       - 輸入：`struct S { int* a[4]; };`
       - 期望：`array_dims=[4]` 且型別為 `pointer`。
     - `test_scalar_pointer_unchanged`：
       - 輸入：`struct S { int* p; };`
       - 期望：仍以原先 tuple 路徑/或 `MemberDef` 表現（不含 `array_dims`）。
   - 佈局測試：`tests/model/test_layout_v15_pointer_array.py`
     - `test_layout_expands_pointer_nd_array`：
       - 使用 `calculate_layout`，輸入成員包含 `{"type":"pointer","name":"arr2d","array_dims":[2,3]}`。
       - 期望：產生 6 個元素 `arr2d[0][0] ... arr2d[1][2]`，每個元素 `type=="pointer"`，`size==pointer_size`。
   - 整合測試（Presenter）：`tests/presenter/test_presenter_v15_pointer_array.py`
     - `test_presenter_tree_nodes_for_pointer_nd_array`：
       - 走 `StructModel.load_struct_from_file` 載入包含 `U8* arr2d[2][3];` 的 .h。
       - 期望：`get_display_nodes("tree")` 中 `arr2d` 節點下有 6 個子節點（名稱正確）。

2) 實作步驟
   - 實作 1：修改 `src/model/struct_parser.py` → `parse_member_line` 的指標分支，如「建議修正」段落所示。
   - 實作 2：若需要，調整 `parse_member_line_v2` 的 dict → `MemberDef` 映射（目前已支援）。
   - 實作 3：驗證 `layout` 已可展開 pointer N-D 陣列（不需變更）。
   - 實作 4：Presenter 走讀與驗證（通常無需修改）。

3) 驗收標準
   - 全部新增測試通過。
   - GUI 實測：選用 `examples/v14_features_example.h`，`arr2d` 正確展開為 6 個子項。
   - 不影響既有測試（回歸乾淨）。



