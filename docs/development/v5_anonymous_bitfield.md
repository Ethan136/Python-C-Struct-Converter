# v5 Anonymous Bitfield（匿名位元欄位）開發規劃

> 本文件為 v5 平行開發子主題之一，總策略請參考 [v5_develop_strategy.md]。
> 本主題需等 AST/物件模型/展平 refactor 完成後再平行開發，相關 AST/展平請參考 v5_nested_struct_union.md。

## 一、開發目標
- parser 能解析匿名 bitfield（name=None），AST 已支援 name=None。（2024/07/09 已完成）
- layout calculator 能正確分配 bit offset，匿名 bitfield 與有名 bitfield 共用 storage unit。（2024/07/09 已完成）
- export/hex parse/GUI 能處理 name=None。（export/hex parse 已完成，GUI 可視需求補齊）

## 二、開發步驟
1. parser 支援匿名 bitfield 語法，AST 已有 name=None。（已完成）
2. layout calculator 支援 bit offset 分配。（已完成）
3. export/hex parse/GUI 支援 name=None。（export/hex parse 已完成）
4. 補齊單元測試與 XML 驅動測試。（單元測試已覆蓋所有匿名 bitfield 關鍵情境）

## 三、測試規劃
- 覆蓋情境：
  - 連續多個匿名 bitfield
  - 匿名與有名 bitfield 混合
  - 巢狀 struct/array 內的匿名 bitfield
  - bitfield 與 array/pragma pack 組合（建議於 v5_integration 分支整合測試）
- XML 驅動多組匿名 bitfield 測資。（可視需求補齊）
- 單元測試已涵蓋匿名 bitfield layout/offset/bit_offset、匯出、hex parse，全部通過。
- 建議測試檔案：`tests/test_struct_model.py`、`tests/test_struct_parser.py`、`tests/test_layout.py`、`tests/xml_struct_model_loader.py`
- 參考測試 stub：
```python
class TestStructModelAnonymousBitfield(unittest.TestCase):
    def test_anonymous_bitfield_layout(self):
        ...
```

## 四、依賴說明與分工
- 本主題需等 AST/物件模型/展平 refactor 完成後再平行開發。
- 若有跨主題 bitfield/array/pragma pack 測試，建議於 v5_integration 分支整合。

## 五、文件/測試同步
- 本文件與 v5_develop_strategy.md、README、STRUCT_PARSING.md 需同步更新。

## 六、功能摘要與移植注意事項（整合自 v5_nested_struct_union_array_pragma.md）

- Parser 支援 `int : 3;` 這種匿名 bitfield，`MemberDef.name=None`。
- regex 與 AST 皆允許名稱省略。
- Layout 能正確分配 bit offset，與有名 bitfield 共用 storage unit。
- 匯出 .h 時，匿名 bitfield 省略名稱（`int : 3;`）。
- 解析 hex 時，結果 list 會包含 `{"name": None, ...}`，可選擇顯示為 "(anon bitfield)"。
- 測試需涵蓋匿名 bitfield layout/offset/bit_offset、匯出、hex parse。
- 建議：
  1. 依據本摘要，分步驟將 parser、layout、export、測試等功能逐一補齊。
  2. 測試可參考 v5 相關測試案例，確保所有匿名 bitfield 情境皆能正確處理。
  3. 文件與 README 也需同步補充。 

## 七、巢狀 struct/union 測資 XML 格式規範（2024/07/09 新增）

- 為確保 AST 與 XML 測資一一對應、完全符合 C++ 巢狀結構語意，所有巢狀 struct/union 成員在 XML 測資中都必須明確標註 `<nested_members>`。
- 規範如下：
  - 只要是 struct/union 型別的成員，必須在 `<member type="struct" name="...">` 或 `<member type="union" name="...">` 下加 `<nested_members>`。
  - 巢狀 struct/union 的所有成員都要完整列出於 `<nested_members>` 內。
  - 即使是空 struct/union，也要 `<nested_members />`。
- 測試程式將嚴格比對 AST 與 XML 的巢狀結構，成員數量、型別、名稱都必須一致。
- 這樣才能完全符合 C++ 的資料結構規範，也方便自動化工具、靜態分析、文件產生等用途。
- 若遇到不一致，應優先修正 XML 測資，而不是讓測試程式寬容。 