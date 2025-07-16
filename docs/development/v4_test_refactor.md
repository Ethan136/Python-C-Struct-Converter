# v4 測試程式碼重構計畫

## 1. 目標
- **擴大自動化測試覆蓋**：將更多 hardcode 的資料驅動測試案例，遷移到 XML 設定檔中。
- **提升測試程式碼的可維護性**：讓測試案例更容易新增、修改與管理。

## 2. 擴大 XML 驅動測試

### 2.1. 優先處理 `test_input_field_processor.py`
- **背景**：此檔案的測試案例最單純，幾乎都是純粹的「輸入-輸出」對應，是 XML 化的最佳起點。
- **計畫 (TDD)**：
    1.  **建立新測試類**：在 `test_input_field_processor.py` 中建立一個新的測試類 `TestInputFieldProcessorXML`,並標記為使用 `unittest.skip` 暫時跳過。
    2.  **擴充 XML**：在 `tests/data/test_input_field_processor_config.xml` 中，新增一個測試案例，對應一個目前在 `TestInputFieldProcessor` 中的 hardcode 測試。
    3.  **修改 Loader**：擴充 `xml_input_field_processor_loader.py`，使其能解析新的測試案例格式。
    4.  **實作新測試**：在 `TestInputFieldProcessorXML` 中，撰寫一個測試方法，使用 loader 載入新的 XML 案例並執行斷言。
    5.  **執行與驗證**：執行測試，確認新的 XML 測試案例通過。
    6.  **移除舊測試**：刪除 `TestInputFieldProcessor` 中對應的 hardcode 測試。
    7.  **重複**：逐步將其他適合的 hardcode 測試案例，重複以上步驟，遷移到 XML 中。

### 2.2. 逐步遷移 `test_struct_model.py`
- **背景**：`test_struct_model.py` 和 `test_struct_model_integration.py` 中，也存在大量適合資料驅動的測試案例。
- **計畫 (TDD)**：
    1.  **識別目標**：從 `test_struct_model.py` 中，挑選一個純資料驗證的測試方法，例如 `test_parse_hex_data_bitfields`。
    2.  **建立新測試類**：建立一個新的測試類 `TestStructModelXML`，並暫時跳過。
    3.  **擴充 XML**：在 `tests/data/test_struct_model_config.xml` 中，新增對應的測試案例，包含 struct 定義、hex 輸入和預期結
    4.  **修改 Loader**：擴充 `xml_struct_model_loader.py` 以支援新的測試案例格式。
    5.  **實作與驗證**：撰寫新的測試方法，載入 XML 並執行斷言，確保測試通過。
    6.  **移除舊測試**：刪除 `test_struct_model.py` 中對應的 hardcode 測試。
    7.  **重複**：逐步遷移其他適合的測試案例。

## 2.3. 測試 code 分資料夾管理建議（2024/07 補充）

- 隨著測試數量與複雜度提升，建議將測試 code 依主題/模組分資料夾管理，提升可維護性與可讀性。
- **建議分法**：
    - `tests/model/`：
        - **分類原則**：涵蓋 Model 層核心邏輯、資料結構、演算法、資料驗證等。
        - **範例**：struct_model、input_field_processor、layout、parser、bitfield、padding、manual struct、integration（僅 model 層）。
    - `tests/view/`：
        - **分類原則**：涵蓋 GUI 行為、Tkinter 互動、View 層元件初始化、UI 驗證等。
        - **範例**：struct_view、struct_view_refactor、struct_view_padding、GUI 互動、tab 切換、debug tab、剩餘空間顯示。
    - `tests/presenter/`：
        - **分類原則**：涵蓋 Presenter 層事件流、狀態管理、View-Model 溝通、錯誤處理等。
        - **範例**：struct_presenter、presenter refactor、cache 行為、layout 計算快取。
    - `tests/integration/`：
        - **分類原則**：跨層整合測試，驗證多層協作、端到端流程。
        - **範例**：struct_model_integration、manual_struct_integration、全流程驗證。
    - `tests/data_driven/`：
        - **分類原則**：所有 XML loader、XML 驅動測試、資料驅動測試類別。
        - **範例**：xml_manual_struct_loader、xml_input_conversion_loader、xml_struct_model_loader、base_xml_test_loader、所有 XML 驅動測試類別。
    - `tests/utils/`：
        - **分類原則**：小型工具、alias、placeholder、union、mock、測試輔助函式等。
        - **範例**：layout_refactor、pack_alignment_placeholder、presenter_refactor、union_preparation、mock presenter/model。
    - `tests/data/`：
        - **分類原則**：所有測試用 XML、.h、mock 檔案。
        - **範例**：test_struct_model_config.xml、test_input_conversion_config.xml、test_struct_parsing_test_config.xml、example.h。
- **遷移步驟建議**：
    1. 規劃好資料夾結構與命名規則。
    2. 批次移動測試檔案，並修正 import 路徑（如 loader、mock、data 路徑）。
    3. 確認 `__init__.py` 存在於每個子資料夾（讓 unittest/pytest 能自動發現）。
    4. 更新 README 與 CI/CD 腳本（如有 hardcode 路徑）。
    5. 執行一次完整測試，確保一切正常。
- **優點**：可維護性提升、主題清晰、CI/CD 更彈性、便於擴充。

## 3. 維持 Hardcode 的測試

- **原則**：對於測試「行為」、「例外處理」和「UI 互動」的案例，繼續維持 hardcode 的方式，因為這類測試難以用純資料描述，硬要 XML 化反而會降低可讀性。
- **範例**：
    - `test_load_struct_from_file_invalid` (例外處理)
    - `test_is_supported_field_size` (API 邊界)
    - `test_struct_view.py` 中的 UI 事件觸發測試 (GUI 行為)

## 4. 進度紀錄

- `test_input_field_processor.py` 已全面使用 `test_input_field_processor_config.xml`，其中 `pad_hex_input` 與 `convert_to_raw_bytes` 測試皆改為 XML 驅動。
- `test_input_conversion.py` 的主要案例改由 `test_input_conversion_config.xml` 與 `test_input_conversion_error_config.xml` 提供。
- `test_struct_parsing_core.py` 完全讀取 `struct_parsing_test_config.xml` 執行。
- `test_struct_manual_integration.py` 與 `test_manual_struct_v3_integration.py` 共同使用 `manual_struct_test_config.xml`。
- `test_struct_model_integration.py` 的多數案例亦由 `test_struct_model_integration_config.xml` 載入。
 - `test_struct_model.py` 現已大幅精簡，多數解析、layout、hex 相關案例均由 `test_struct_model_config.xml` 載入。
- 目前仍有多項 hardcode 測試（如 `test_string_parser.py`、`test_struct_parser_v2.py`、`test_layout_refactor.py`、`test_pack_alignment_placeholder.py`、`test_presenter_refactor.py`、`test_struct_presenter.py`、`test_union_preparation.py`、各 GUI 測試以及部分 sanity check），主要涵蓋例外處理與 UI 行為。