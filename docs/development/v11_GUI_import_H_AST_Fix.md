# v11 - GUI 匯入 .H 使用 AST 解析修正

## 背景與症狀

- 在 GUI 以「載入 .h 檔」匯入 `examples/v5_features_example.h` 時，Struct Layout 只顯示到部分頂層欄位（如 `arr2d`、`b2`、`tail`），缺少 `nested.x`、`nested.y`、`nested.inner_union.*` 與 `arr2d[i][j]` 等展開結果。
- 解析出來的 offset/size 與真實 C/C++ 佈局不一致，導致後續值解析與檢視錯誤。

## 問題原因（Root Cause）

- 舊有的匯入流程在 `src/model/struct_model.py::load_struct_from_file()` 中，使用「平面/正規表達式」的 parser：`parse_struct_definition(content)`。
  - 這條 parser 只回傳 tuple/dict 的平面成員；對巢狀 struct/union 只放入簡化佔位（例如 `("struct", var_name)`），不保留內部 `members`。
  - 後續 `calculate_layout(...)` 的 legacy 分支雖會做展平，但因為巢狀的完整結構已遺失，無法正確展開巢狀成員與多維陣列，造成 GUI 僅顯示頂層項目。

## 修正方式（What Changed）

- 將 `.h` 匯入流程改為「優先使用 AST 解析，再回退舊版解析」。
  - 先嘗試 `parse_c_definition_ast(content)`，取得 `StructDef/UnionDef` 與 `MemberDef`（含 `array_dims`、`nested`、bitfield 資訊）。
  - 若 AST 解析成功：
    - 設定 `self.struct_name = definition.name`、`self.ast = definition`、`self.members = list(definition.members)`。
    - 呼叫 `calculate_layout(self.members)`。當 `members` 為 AST 物件時，版面計算會走 `StructLayoutCalculator/UnionLayoutCalculator`，遞迴正確展開巢狀結構、union 與多維陣列，並計算對齊與 padding。
  - 若 AST 解析失敗，再回退舊有 `parse_struct_definition(content)` 的路徑，確保相容性。

### 主要程式變更位置

- 檔案：`src/model/struct_model.py`
- 函式：`load_struct_from_file(self, file_path)`

核心邏輯（節錄）：

```python
with open(file_path, 'r') as f:
    content = f.read()
self.struct_content = content

try:
    from src.model.struct_parser import parse_c_definition_ast
    definition = parse_c_definition_ast(content)
except Exception:
    definition = None

if definition and hasattr(definition, 'name') and hasattr(definition, 'members'):
    self.struct_name = definition.name
    self.ast = definition
    self.members = list(definition.members)
    self.layout, self.total_size, self.struct_align = calculate_layout(self.members)
else:
    struct_name, members = parse_struct_definition(content)
    if not struct_name or not members:
        raise ValueError("Could not find a valid struct definition in the file.")
    self.struct_name = struct_name
    self.members = self._convert_to_cpp_members(members)
    self.layout, self.total_size, self.struct_align = calculate_layout(self.members)
```

## 成果（After）

- 匯入 `examples/v5_features_example.h` 時：
  - `nested.x`、`nested.y`、`nested.inner_union.u1/u2` 正確出現在 Layout；
  - `arr2d[2][3]` 展開為 `arr2d[i][j]` 各元素，offset/size 正確；
  - bitfield（含匿名 bitfield）維持正確的 storage unit 打包與 `bit_offset` 計算。

## 相容性與限制

- 舊 `.h` 檔案若 AST 解析失敗會自動回退舊版解析流程，維持相容性。
- `#pragma pack` 指示目前尚未由 GUI 層提供設定；版面計算類別支援 `pack_alignment` 參數，但預設不啟用。後續可考慮在 GUI/Presenter 層提供設定入口。

## 後續追蹤（Follow-ups）

- 若在 GUI 刷新過程遇到 Treeview IIDs 重複的例外（`TclError: Item ... already exists`），可檢視 Presenter 的 debounce 推送與 View 的清除/重繪流程，確保重繪前完整清空或產生新的節點 ID（此項與本次 AST 解析修正無直接邏輯關聯）。


