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