# v5 Develop Strategy（平行開發總規劃）

本文件規劃 v5 重大功能（AST/物件模型/展平 refactor、N-D array、anonymous bitfield、pragma pack）之平行開發策略，明確標示各主題依賴關係、分工建議與合併流程，供多位開發人員協作參考。

---

## 1. 開發主題與分工

| 主題 | 文件 | 建議分工 | 依賴 | 可否平行 |
|------|------|----------|------|----------|
| 巢狀 struct AST/物件模型/展平 refactor | v5_nested_struct.md | 1人主導 | 無 | 必須最先完成 |
| union AST/物件模型/展平 refactor | v5_union.md | 1人主導 | 巢狀 struct 完成 | 平行 |
| N-D array（多維陣列） | v5_nd_array.md | 1人主導 | 巢狀 struct 完成 | 平行 |
| anonymous bitfield（匿名位元欄位） | v5_anonymous_bitfield.md | 1人主導 | 巢狀 struct 完成 | 平行 |
| pragma pack/pack_alignment | v5_pragma_pack.md | 1人主導 | 巢狀 struct 完成 | 平行 |

---

## 2. 開發順序與依賴

1. **巢狀 struct AST/物件模型/展平 refactor**
   - 先完成巢狀 struct AST/物件模型遞迴巢狀、展平能力。
   - 完成後，通知 union、N-D array、anonymous bitfield、pragma pack 等主題可開始平行開發。

2. **union、N-D array、anonymous bitfield、pragma pack**
   - 於巢狀 struct refactor 完成後，各自建立分支平行開發。
   - 各自補齊 parser、layout、export、GUI、測試。

3. **整合測試與合併**
   - 各主題分支完成後，統一合併到 v5_integration 分支。
   - 進行整合測試、衝突解決、最終修正。

---

## 3. 建議 git branch 流程

```
main
 │
 ├─ v5_ast_refactor（基礎，完成 AST/物件模型/展平能力）
 │    ├─ v5_nd_array
 │    ├─ v5_anonymous_bitfield
 │    ├─ v5_pragma_pack
 │
 └─ v5_integration（整合所有 v5 主題，最終測試/修正）
```

---

## 4. 測試與文件同步
- 各主題分支皆需補齊單元測試、XML 驅動測試。
- 文件（各主題 md、README、STRUCT_PARSING.md）需同步補充。
- v5_integration 分支需進行全功能整合測試。

---

## 5. 協作與合併建議
- 各主題分支應定期與 v5_ast_refactor/main 同步，減少合併衝突。
- 合併到 v5_integration 前，請先確保測試全通過。
- 整合測試階段，需協作解決跨主題衝突與覆蓋率缺口。

---

## 6. 參考文件
- development/v5_nested_struct.md
- development/v5_union.md
- development/v5_nd_array.md
- development/v5_anonymous_bitfield.md
- development/v5_pragma_pack.md 