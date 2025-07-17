# v5 巢狀 struct AST/物件模型/展平 Refactor 開發規劃

> 本文件為 v5 平行開發子主題之一，總策略請參考 [v5_develop_strategy.md]。
> 本主題為所有 v5 功能的基礎，相關 union、N-D array、anonymous bitfield、pragma pack 請參考對應主題文件。

## 一、開發目標
- AST/物件模型能遞迴描述巢狀 struct，支援多層巢狀。
- parser 能遞迴解析巢狀 struct，並正確建立 AST。
- layout calculator 能展平巢狀 struct 結構，正確計算 offset/align。
- export/hex parse/GUI 能處理展平後的名稱。

## 二、開發步驟
1. Refactor AST/物件模型，支援 nested struct。
2. parser 支援巢狀 struct 的遞迴解析。
3. layout calculator 支援展平巢狀 struct，offset/align 正確。
4. export/hex parse/GUI 支援展平名稱。
5. 補齊單元測試與 XML 驅動測試。

## 三、測試規劃
- 覆蓋情境：
  - 多層巢狀 struct
- XML 驅動多組巢狀 struct 測資。
- 建議測試檔案：`tests/model/test_struct_ast_refactor.py`（巢狀 struct 部分）
- 參考測試 stub：
```python
class TestStructModelNested(unittest.TestCase):
    def test_nested_struct_layout(self):
        ...
```

## 四、依賴說明與分工
- 本主題需最先完成，其他主題（union、N-D array、anonymous bitfield、pragma pack）需等本功能完成後再平行開發。
- 若有大規模 AST/物件模型 refactor，請先與其他主題負責人協調，減少 merge 衝突。
- 合併到 v5_integration 前，請先與 main/v5_ast_refactor 分支同步。

## 五、文件/測試同步
- 本文件與 v5_develop_strategy.md、README、STRUCT_PARSING.md 需同步更新。

## 六、本階段功能範圍說明（2024/07 MVP）

- 本階段（AST/物件模型/展平 refactor MVP）僅聚焦於支援巢狀 struct（`struct Name { ... } var;`）。
- parser 僅需能遞迴解析巢狀 struct，並正確建立 AST（`MemberDef.nested` 掛載 `StructDef`）。
- union、array、匿名 struct/bitfield 等進階情境將於本主題完成後，於各自主題分支平行開發。
- 測試以巢狀 struct 為主，確保 AST 能正確描述多層巢狀結構。
- 文件、測試、程式碼請明確標註本階段僅支援巢狀 struct，避免誤用未支援語法。 

## 七、巢狀 struct parser 重構設計（TDD 流程）

### 目標
- 僅支援 `struct Name { ... } var;` 巢狀結構，正確建立 AST（`MemberDef.nested` 掛載 `StructDef`）。
- 其他語法（union/array/bitfield/匿名 struct）暫不處理。

### 遞迴解析策略
1. 解析 struct body 時，逐字元掃描，遇到 `struct Name { ... } var;`：
   - 擷取巢狀 struct 名稱（Name）、內容（{...}）、變數名稱（var）。
   - 遞迴呼叫 `parse_struct_definition_ast` 解析巢狀內容。
   - 建立 `MemberDef(type="struct", name=var, nested=巢狀StructDef)` 加入 members。
2. 其他欄位維持現有解析方式。
3. 僅處理有名稱的巢狀 struct 欄位。

### 流程草圖
- 逐字元掃描 struct body：
  1. 若遇到 `struct` 關鍵字，判斷是否為巢狀 struct 宣告。
  2. 若是，找到對應大括號範圍，擷取內容與變數名稱。
  3. 遞迴解析巢狀內容，建立 AST。
  4. 跳過已處理區段，繼續掃描。
  5. 其餘欄位用現有 parse_member_line_v2 處理。

### 注意事項
- 僅支援 `struct Name { ... } var;`，不支援匿名 struct/union/array/bitfield。
- 測試以 `tests/model/test_struct_ast_refactor.py` 巢狀 struct 部分為主。
- 每次重構後立即執行測試，確保逐步綠燈。 