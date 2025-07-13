# v4_test_refactor.md

## 1. 目前測試架構概述

本專案測試分為數個層次：
- 單元測試（如 input 處理、struct 解析、GUI 行為）
- 整合測試（如 struct parsing 與 input 處理整合）
- 自動化資料驅動測試（以 XML 配置檔案描述測試案例）

### 主要測試檔案分類
- `test_input_conversion.py`：支援 XML 驅動的自動化測試（`tests/data/test_config.xml`）
- `test_struct_parsing_core.py`：支援 XML 驅動的自動化測試（`tests/data/struct_parsing_test_config.xml`）
- 其他如 `test_struct_model.py`、`test_struct_model_integration.py`、`test_input_field_processor.py`、`test_string_parser.py` 等，主要為 hardcode 測試案例

## 2. 測試資料抽離現況

### 已經 XML 化的測試
- **Input 轉換測試**
  - 測試名稱、input、expected result 皆定義於 `tests/data/test_config.xml`
  - 測試程式自動讀取 XML，動態產生所有測試案例
- **Struct parsing 核心測試**
  - 測試名稱、struct 檔案、input、expected result 皆定義於 `tests/data/struct_parsing_test_config.xml`
  - 測試程式自動讀取 XML，動態產生所有測試案例

### 尚未 XML 化的測試
- **StructModel/Presenter/GUI 相關測試**
  - 例如 `test_struct_model.py`、`test_struct_model_integration.py`、`test_struct_view.py`、`test_input_field_processor.py`、`test_string_parser.py` 等
  - 測試案例（test name、input、expected result）多為 hardcode 在 Python 測試 code 內
  - 這些測試多數為：
    - 驗證 class 初始化、狀態、例外處理、GUI 行為、mock presenter/view 等
    - 或針對特殊邏輯（如 bitfield packing、padding、GUI event）進行細部驗證

## 3. 是否能全面 XML 化？

### 適合 XML 化的測試類型
- **資料驅動、純 input/output 驗證的測試**
  - 例如：input 轉換、struct parsing、資料欄位驗證、格式轉換等
  - 已經 XML 化的部分運作良好，擴充性佳

### 不適合 XML 化的測試類型
- **複雜互動、狀態驗證、GUI 行為、mock 驗證**
  - 例如：GUI event、mock presenter/view 呼叫、例外處理、物件狀態驗證
  - 這類測試需驗證物件行為、例外、UI 狀態，難以用純資料描述
  - 強行 XML 化會讓測試程式變得複雜且難維護

### 綜合建議
- **維持現有混合模式**：
  - 資料驅動測試（input/output 驗證）持續 XML 化，利於擴充與維護
  - 行為/互動/例外/GUI 測試維持 hardcode，保持可讀性與彈性
- **可考慮進一步將部分驗證規則、錯誤訊息等抽離至 YAML/XML/JSON，但不建議所有測試都 XML 化**

## 4. 建議 refactor 步驟
1. **檢查現有 hardcode 測試**，若屬於純 input/output 驗證，可考慮移至 XML
2. **維持行為/互動/例外/GUI 測試於 code 內**，僅將可結構化資料抽離
3. **撰寫自動化工具**，協助產生/驗證 XML 測試資料與測試 code 的一致性

## 5. 結論
- 專案已經在 input/struct parsing 層面實現高比例 XML 測試資料抽離，架構良好
- 其他測試（如 GUI、mock、例外）維持 code 內 hardcode，較為合理
- 未來可持續優化 XML 測試資料結構，並撰寫工具協助管理 

## 6. 進一步 XML 化規劃與流程

### 6.1 需調整的測試檔案與 code
- `tests/test_struct_model.py`
  - 解析 struct 定義、bitfield、padding、pointer、混合欄位等資料處理型測試
  - 目前 struct 定義、input、expected output 多 hardcode 在 code 內
- `tests/test_struct_model_integration.py`
  - 各種 struct loading、hex parsing、bitfield、pointer、padding、short input 等整合測試
  - 目前 struct 定義、input、expected output 多 hardcode 在 code 內
- `tests/test_input_field_processor.py`
  - 各種 input/output 對應組合、padding、raw bytes 轉換、大小端、錯誤處理等
  - 目前 test_cases 以 Python list 寫在 code 內
- 可能需擴充/新增 XML config 檔案（如 tests/data/model_test_config.xml）
- 需調整/擴充測試 loader，支援新 XML 格式

### 6.2 Refactor 流程規劃（TDD 變體）
1. **設計/實作新的 XML 驅動測試機制**
   - 設計 XML schema，能描述 struct 定義、input、expected output
   - 新增 XML config 檔案，先覆蓋部分現有 hardcode 測試案例
   - 新增 Python loader，能自動讀取 XML 並產生 unittest 測試
   - 舊的 hardcode 測試暫時保留
2. **新舊測試機制並行驗證**
   - 執行新舊測試，確保同一組 input/output 結果一致
   - 若有不一致，回到步驟 1 修正 loader/schema/測試資料
3. **逐步遷移與驗證**
   - 當新機制穩定且覆蓋率足夠，逐步移除對應的 hardcode 測試
   - 最終僅保留必要的行為/例外/GUI 測試於 code 內

### 6.3 建議 XML schema（範例）
```xml
<model_tests>
  <test_case name="bitfield_basic" description="Test struct with bitfields">
    <struct_definition><![CDATA[
      struct A {
        int a : 1;
        int b : 2;
        int c : 5;
      };
    ]]></struct_definition>
    <input_data>
      <hex>8d000000</hex>
    </input_data>
    <expected_results>
      <member name="a" value="1"/>
      <member name="b" value="2"/>
      <member name="c" value="17"/>
    </expected_results>
  </test_case>
  <!-- 更多案例... -->
</model_tests>
```

### 6.4 需動到的 code 列表
- `tests/test_struct_model.py`：重構部分測試為 XML 驅動
- `tests/test_struct_model_integration.py`：重構部分測試為 XML 驅動
- `tests/test_input_field_processor.py`：重構 test_cases 為 XML 驅動
- 新增/擴充 XML config 檔案（如 tests/data/model_test_config.xml）
- 新增/擴充 Python loader（如 TestModelConfigLoader）
- 測試 README、開發文件同步更新

### 6.5 流程圖
1. 設計 XML schema → 2. 新增 XML 測試資料 → 3. 實作 loader → 4. 新舊測試並行 → 5. 驗證一致性 → 6. 遷移/移除 hardcode 測試

---

（本節可隨 refactor 進度持續補充細節與經驗） 

## 7. 優先順序與判斷依據

### 為什麼先處理 test_input_field_processor.py？
- **單純資料處理**：此檔案測試幾乎全為 input/output 對應，無複雜 struct 解析或跨檔案依賴。
- **現有測試結構簡單**：大多數測試為 list of tuples，直接搬到 XML 最容易。
- **不影響其他測試流程**：此模組測試與其他 struct parsing、integration 測試幾乎無耦合，改動風險低。
- **驗證新 loader 機制最容易**：可快速驗證 XML schema、loader、unittest 整合流程。

### 建議優化順序
1. 先進行 `test_input_field_processor.py` 的 XML 化 refactor
2. 等 loader 機制穩定後，再推進 `test_struct_model.py`、`test_struct_model_integration.py` 等較複雜的資料驅動化

--- 

## 8. pytest 執行常見問題

pytest 執行常見問題與解法，請見 tests/README.md。 