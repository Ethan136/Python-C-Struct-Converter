# v5 Post Test Refactor（AST/TDD 重構後測試規劃）

## 1. 目標
- **強化 AST/Parser 測試覆蓋率**：涵蓋巢狀 struct/union/array、匿名 struct/union、N-D array、bitfield 等情境。
- **推動 XML 驅動測試**：將重複、資料驅動測試集中於 XML，提升可維護性。
- **抽象共用驗證 helper**：遞迴比對 AST 結構、展平結果，減少重複驗證邏輯。
- **測試分層與主題分類**：依 model/view/presenter/integration/data_driven/utils 分層管理測試。
- **平行開發測試同步**：各主題分支測試規劃、stub、TDD 流程明確，便於協作。

## 2. AST/Parser 測試重構重點

### 2.1 巢狀 struct/union/array
- 以 TDD 流程重構 `parse_struct_definition_ast`，逐步讓巢狀 struct 測試綠燈。
- 測試涵蓋：
    - 巢狀 struct/union/array
    - 匿名 struct/union（暫 skip，待後續主題）
    - N-D array（暫 skip，待後續主題）
    - 匿名 bitfield（暫 skip，待後續主題）
- 驗證方式：
    - 遞迴比對 AST 結構
    - 展平成員名稱
    - XML 驅動測試（建議）

### 2.2 XML 驅動測試
- 將重複、資料驅動測試集中於 XML，減少 hardcode 測試。
- 測試資料建議集中於 `tests/data/`，格式與 v4 相容。
- Loader/驗證 helper 建議抽象共用，便於各主題複用。

### 2.3 測試分層與主題分類
- 依 v4 建議，測試分為 model/view/presenter/integration/data_driven/utils/data。
- 各主題測試檔案明確標註覆蓋重點、XML 驅動整合方式。
- 測試 stub、TDD 流程、XML 驅動建議同步補充於主題文件。

## 3. 平行開發測試同步建議
- 各主題分支（如 union、N-D array、bitfield、pragma pack）應：
    - 依主題文件規劃 stub、TDD 流程、XML 驅動測試。
    - 測試 stub/skip 明確，便於後續恢復。
    - 共用驗證 helper 集中於 utils，減少重複。
    - 測試資料集中於 data/，便於管理。
- 合併前，建議以 pytest/CI/CD 驗證全測試綠燈。

## 4. 進度與後續建議
- 巢狀 struct AST/TDD 重構已完成，測試全綠。
- 進階主題測試（union/array/bitfield/pragma pack）可依分支平行開發，stub/skip 明確。
- 測試與文件同步，建議逐步精簡、集中 XML 驅動、抽象共用驗證邏輯。
- 持續檢查覆蓋率，補齊 edge case。

## 5. 參考文件
- v5_nested_struct.md
- v5_union.md
- v5_nd_array.md
- v5_anonymous_bitfield.md
- v5_pragma_pack.md
- v4_test_refactor.md 