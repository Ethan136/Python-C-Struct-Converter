# v7 巢狀 union/匿名 struct/union/N-D array AST/flatten Refactor 規劃

## 一、開發目標
- AST/物件模型能遞迴描述巢狀 union、匿名 struct/union、N-D array。
- parser 能遞迴解析巢狀 union/匿名 struct/union/N-D array，並正確建立 AST。
- layout calculator 能展平巢狀 union/struct/array 結構，正確計算 offset/align。
- 匿名 struct/union/bitfield 能正確展平、命名、匯出、hex parse。
- XML 驅動測試能完整覆蓋所有巢狀/匿名/多維情境。

## 二、開發步驟
1. parser 支援巢狀 union/匿名 struct/union/N-D array 語法，AST 能正確遞迴。
2. layout calculator 支援展平巢狀 union/struct/array，offset/align 正確。
3. 匿名 struct/union/bitfield 展平命名規則、匯出、hex parse。
4. XML 驅動測試補齊所有 edge case。
5. 文件、測試、程式碼需明確標註支援範圍。

## 三、測試規劃
- 覆蓋情境：
  - 巢狀 union/struct/array
  - 匿名 struct/union/bitfield
  - N-D array 與巢狀 struct/union 組合
  - union/struct/array/bitfield 混合
- XML 驅動多組巢狀/匿名/N-D array 測資。
- 測試檔案：`tests/model/test_struct_ast_refactor.py`、`tests/model/test_struct_model.py`、`tests/data/` XML。

## 四、依賴與分工
- 依賴 v5_nested_struct.md、v5_union.md、v5_nd_array.md、v5_anonymous_bitfield.md。
- 建議分工：parser、layout、export、測試、XML schema。

## 五、文件/測試同步
- 本文件與 v5_develop_strategy.md、README、STRUCT_PARSING.md 需同步更新。
- 每次 edge case/功能補齊，需同步更新 XML 測資與文件。

## 六、目前狀態與 TODO
- [x] 巢狀 union/struct/array AST/flatten 已完成
- [x] 匿名 struct/union/bitfield AST/flatten 已完成
- [x] N-D array 巢狀展平已完成
- [x] XML 驅動測試已覆蓋
- [x] 測試 stub/skip 已解除

---

> 本文件為 v7 平行開發子主題之一，總策略請參考 v5_develop_strategy.md。
> 若有跨主題 array/bitfield/pragma pack 測試，建議於 v7_integration 分支整合。 