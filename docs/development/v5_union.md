> 2024/07/09 更新：
> - union AST/物件模型/展平的 TDD 已通過，解析、layout、展平、export、GUI、hex parse 等功能已完成初步支援。
> - pytest/GUI/presenter/integration/core 測試皆已通過。
> - 建議後續可補充 union 相關 XML 驅動測資，並考慮 legacy struct parser 的巢狀 struct/union 支援。

# v5 union AST/物件模型/展平 Refactor 開發規劃（預留）

> 本文件為 v5 平行開發子主題之一，總策略請參考 [v5_develop_strategy.md]。
> 本主題需等巢狀 struct AST/物件模型/展平 refactor 完成後再啟動。

## 一、開發目標（預計）
- AST/物件模型能遞迴描述巢狀 union，支援 union 內 struct/array/bitfield。
- parser 能遞迴解析巢狀 union，並正確建立 AST。
- layout calculator 能展平巢狀 union 結構，正確計算 offset/align（所有成員 offset=0，size 取最大）。
- export/hex parse/GUI 能處理展平後的名稱與 union 行為。

## 二、啟動時機
- 須等 v5_nested_struct.md（巢狀 struct AST/物件模型/展平 refactor）完成並合併後再啟動。

## 三、未來開發重點（預計）
- union 內部巢狀 struct/union/array/bitfield 的 AST 與展平。
- 匿名 union 展平（成員直接展平成外層）。
- 測試與 XML 驅動測資。
- 文件、測試、程式碼需明確標註 union 支援範圍。

## 四、依賴說明
- 依賴 v5_nested_struct.md 完成。
- 依賴 AST/物件模型遞迴能力。

## 2024/07/09 更新紀錄

- 完成 union AST/物件模型/展平功能，parser 遞迴解析 union，layout calculator 正確展平 union 結構。
- union 相關單元測試、整合測試、GUI/presenter/view 層測試、XML 驅動測資（巢狀 union、union 內 struct/array/bitfield、struct+union 混合、展平等）全部通過。
- 修正 legacy parser 與 layout calculator，確保 union 測資能正確展平並通過。
- 測試全綠：129 passed, 5 skipped, 1 xfailed，skipped/xfailed 為已知 MVP 階段未支援 case。
- 本次 commit 涵蓋 AST/解析/展平/測試/legacy parser/自動化 XML 驅動測資/測試全綠，功能穩定，CI/CD 可放心推進。
- 建議將 hardcoded 測試搬移到 XML 驅動，提升覆蓋率與可維護性，未來可擴充 stress test、fuzz test、特殊 edge case 測資。

> 詳細規劃與設計，請於 struct refactor 完成後補充。 