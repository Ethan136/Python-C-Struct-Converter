# v4 Data Type Refactor 計畫

## 一、改動原因與長期優勢

本次 refactor 目標為**完全移除 struct member 的舊格式（如 byte_size、_convert_legacy_member 等相容邏輯）**，統一所有 struct member 為 V3/V4 標準格式（必須有 type/name/bit_size）。

### 改動原因
- 減少程式碼複雜度，移除 legacy/相容橋接，降低維護成本
- 測試、GUI、XML、匯入/匯出等資料流統一格式，避免隱性 bug
- 方便未來擴充新型別、bitfield、array 等功能
- 新進開發者更容易理解與維護

### 長期優勢
- **單一資料結構**：所有 member 都有 type/name/bit_size，無需再判斷 byte_size 或 legacy 欄位
- **程式碼更簡潔**：移除 _convert_legacy_member、byte_size 推斷等橋接邏輯
- **測試與資料一致**：XML、GUI、測試、匯入/匯出皆用同一格式
- **易於 refactor/擴充**：未來如要支援新型別、bitfield 規則、array 等，只需針對新格式設計

---

## 二、改動流程規劃

1. **全專案 grep/檢查**：搜尋 `byte_size`、`_convert_legacy_member`、`is_legacy` 等 legacy 關鍵字，確認所有資料來源都已新格式
2. **同步 refactor**：
    - 移除 struct_model.py 內所有 legacy/相容邏輯
    - 移除/重構 loader、GUI、測試、XML 內的舊格式欄位
3. **全測試驗證**：執行 run_all_tests.py，確保所有測試通過
4. **文件/README 更新**：明確標註 struct member 僅支援新格式
5. **Code Review/PR**：團隊審查，確認無遺漏

---

## 三、需改動的所有地方清單

### 1. 核心邏輯
- `src/model/struct_model.py`：
    - 刪除 `_convert_legacy_member`、`byte_size` 推斷、舊格式相容註解
    - `_convert_to_cpp_members` 僅接受有 type 的 member
    - `export_manual_struct_to_h`、`validate_manual_struct`、`calculate_manual_layout` 等不再處理 byte_size

### 2. 測試/Loader/XML
- `tests/xml_manual_struct_loader.py`、`tests/xml_input_conversion_loader.py`、`tests/xml_input_field_processor_loader.py` 等 loader：
    - 僅產生/消費新格式（type/name/bit_size）
    - XML schema 不再允許 byte_size 欄位
- `tests/data/*.xml`：
    - 移除所有 `<member ... byte_size=... />`，改為 type/bit_size 格式
- `tests/test_struct_manual_integration.py`、`test_struct_model.py` 等：
    - 測試資料、assertion 皆用新格式

### 3. GUI/前端
- struct member 新增/編輯流程：
    - 僅產生 type/name/bit_size 欄位
    - 不再產生 byte_size
- 匯入/匯出 struct：
    - 只支援新格式

### 4. 文件/說明
- `README.md`、`tests/README.md`、`docs/` 內所有 struct member 格式說明
    - 明確標註僅支援新格式

---

> **備註**：
> 若未來有外部資料來源（如舊版 GUI 匯入），需同步升級格式，否則將無法相容。 

---

## 四、測試程式細節修正紀錄

### tests/test_struct_view.py
- Line 27: `used_bits = sum(m.get("byte_size", 0) * 8 + m.get("bit_size", 0) for m in members)`
  - **修正建議**：移除 else 分支，PresenterStub 只計算 type/bit_size，不再支援 byte_size。
- Line 59: `self.assertEqual(self.view.members[1]["byte_size"], 7)`
  - **修正建議**：移除或改為驗證 type/bit_size。
- Line 174: `self.assertEqual(self.view.members[1]["byte_size"], 8)`
  - **修正建議**：移除或改為驗證 type/bit_size。 

---

## 五、2024/06/XX 進度紀錄：XML 驅動測試全面遷移與 legacy 移除

### 1. 測試全面 XML 化
- 所有核心、例外、單元測試（input conversion, field processor, struct parsing）皆已改為 XML 驅動格式。
- 僅 GUI、static data、mocking 測試維持 hardcoded，並於文件註明原因。
- 測試 XML schema 統一，所有 loader 皆繼承 BaseXMLTestLoader，便於擴充與維護。

### 2. Legacy code/data format 移除
- 全專案已無 byte_size、_convert_legacy_member 等 legacy 欄位與橋接邏輯。
- GUI、Presenter、Loader、測試、XML 全面統一 type/name/bit_size 格式。
- 所有測試資料、assertion、mock 皆已同步修正。

### 3. 測試修正與驗證
- 移除 legacy 支援後，針對失敗測試逐一修正資料與 assertion。
- run_all_tests.py 全數通過，確認 C++ 標準 struct/bitfield 行為。

### 4. 文件與後續建議
- README、tests/README.md、docs/ 皆已更新，說明 struct member 僅支援新格式。
- 建議後續可針對 GUI 測試進行自動化、CI/CD、coverage 強化。 