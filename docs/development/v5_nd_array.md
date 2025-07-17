# v5 N-D Array（多維陣列）開發規劃

> 本文件為 v5 平行開發子主題之一，總策略請參考 [v5_develop_strategy.md]。
> 本主題需等 AST/物件模型/展平 refactor 完成後再平行開發，相關 AST/展平請參考 v5_nested_struct_union.md。

## 一、開發目標
- parser 能正確解析多維陣列語法，AST 已支援 array_dims。
- layout calculator 能展平成所有元素，offset/align 正確。
- export/hex parse/GUI 能處理展平後的名稱。

## 二、開發步驟
1. parser 支援多維陣列語法，AST 已有 array_dims 欄位。
2. layout calculator 支援多維展開，offset/align 正確。
3. export/hex parse/GUI 支援展平名稱。
4. 補齊單元測試與 XML 驅動測試。

## 三、測試規劃
- 覆蓋情境：
  - 單層、多層、多維陣列
  - 巢狀 struct/union/array 的多維展開
  - array 與 bitfield/pragma pack 組合（建議於 v5_integration 分支整合測試）
- XML 驅動多組多維陣列測資。
- 建議測試檔案：`tests/test_struct_model.py`、`tests/test_struct_parser.py`、`tests/test_layout.py`、`tests/xml_struct_model_loader.py`
- 參考測試 stub：
```python
class TestStructModelNDArray(unittest.TestCase):
    def test_nd_array_layout(self):
        ...
```

## 四、依賴說明與分工
- 本主題需等 AST/物件模型/展平 refactor 完成後再平行開發。
- 若有跨主題 array/bitfield/pragma pack 測試，建議於 v5_integration 分支整合。

## 五、文件/測試同步
- 本文件與 v5_develop_strategy.md、README、STRUCT_PARSING.md 需同步更新。

## 六、功能摘要與移植注意事項（整合自 v5_nested_struct_union_array_pragma.md）

- Parser 能解析如 `int arr[2][3];`、`struct S { int x; } matrix[2][2];` 等多維陣列。
- Layout 能展平成所有元素（如 `matrix[0][0].x`、`matrix[1][1].x`）。
- 測試需涵蓋多維陣列巢狀 struct/union 的 layout 與解析。
- 建議：
  1. 依據本摘要，分步驟將 parser、layout、export、測試等功能逐一補齊。
  2. 測試可參考 v5 相關測試案例，確保所有多維情境皆能正確處理。
  3. 文件與 README 也需同步補充。 

## 七、TDD 實作紀錄（2024/07 補充）

- **步驟一：新增失敗測試**
  - 已於 `tests/model/test_struct_model.py` 新增 `TestStructModelNDArray.test_nd_array_layout`，驗證 `int arr[2][3];` 應展開為 6 個元素（arr[0][0]~arr[1][2]）。
  - 已新增 `test_nested_struct_with_nd_array_layout`，驗證 `struct S { int x; }; struct NDArrayTest { struct S arr[2][2]; };` 應展開為 4 個元素（arr[0][0].x ~ arr[1][1].x）。
  - 目前 parser 僅支援單一 struct 定義，巢狀 struct array 測試需手動構造 AST 並補 nested 型別。
- **步驟二：實作多維展開與巢狀展平**
  - layout calculator 已支援多維展開與巢狀 struct/array 遞迴展平，產生正確名稱、offset、size。
  - 測試已通過，layout 結構正確。
- **步驟三：建議未來擴充**
  - parser 可擴充 symbol table 支援多 struct 定義與型別查找，讓 nested struct array 測試更自動化。
  - 文件與測試可同步補充更複雜巢狀 struct/array/bitfield 組合案例。

## 八、目前 N-D Array 功能狀態（2024/07 補充）

- 多維陣列（N-D Array）展開、巢狀 struct/array 遞迴展平功能已完成，所有單元測試與 TDD 驗證皆通過。
- 支援任意維度 array、巢狀 struct array，layout 能正確產生所有元素名稱、offset、size。
- 測試涵蓋單層、多層、多維陣列、巢狀 struct/array。
- 目前 parser 僅支援單一 struct 定義，巢狀 struct array 測試需手動構造 AST 並補 nested 型別。
- 後續可擴充 symbol table 型別查找、bitfield/pragma pack 組合、XML 驅動測試等進階情境。

--- 