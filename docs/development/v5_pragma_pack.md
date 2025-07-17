# v5 Pragma Pack/pack_alignment 開發規劃

> 本文件為 v5 平行開發子主題之一，總策略請參考 [v5_develop_strategy.md]。
> 本主題需等 AST/物件模型/展平 refactor 完成後再平行開發，相關 AST/展平請參考 v5_nested_struct_union.md。

## 一、開發目標
- parser 能解析 pragma pack 指令，AST 已能記錄 pack 設定。
- layout calculator 能根據 pack_alignment 動態調整 offset/align。
- export/hex parse/GUI 能處理 pack 設定。

## 二、開發步驟
1. parser 支援 pragma pack 語法，AST 已能記錄 pack 設定。
2. layout calculator 支援 pack_alignment。
3. export/hex parse/GUI 支援 pack 設定。
4. 補齊單元測試與 XML 驅動測試。

## 三、測試規劃
- 覆蓋情境：
  - 不同 pack 值（1/2/4/8）
  - pack 與 array/bitfield/巢狀 struct 組合
  - 與 N-D array/anonymous bitfield 組合（建議於 v5_integration 分支整合測試）
- XML 驅動多組 pragma pack 測資。
- 建議測試檔案：`tests/test_struct_model.py`、`tests/test_struct_parser.py`、`tests/test_layout.py`、`tests/xml_struct_model_loader.py`
- 參考測試 stub：
```python
class TestStructModelPragmaPack(unittest.TestCase):
    def test_pragma_pack_layout(self):
        ...
```

## 四、依賴說明與分工
- 本主題需等 AST/物件模型/展平 refactor 完成後再平行開發。
- 若有跨主題 pack/array/bitfield 測試，建議於 v5_integration 分支整合。

## 五、文件/測試同步
- 本文件與 v5_develop_strategy.md、README、STRUCT_PARSING.md 需同步更新。

## 六、功能摘要與移植注意事項（整合自 v5_nested_struct_union_array_pragma.md）

- 若有 pragma pack 支援，layout 計算時需考慮 pack alignment。
- 本次 diff 以 layout/offset/align 為主，未見明顯 pragma pack 實作，僅以標準 C/C++ 對齊規則為主。
- 建議：
  1. 若需支援 pragma pack，parser/AST 需能記錄 pack 設定，layout 計算需根據 pack_alignment 動態調整 alignment。
  2. 測試需涵蓋 pack=1/2/4/8 等情境。
  3. 文件需明確標示目前支援範圍與限制。 